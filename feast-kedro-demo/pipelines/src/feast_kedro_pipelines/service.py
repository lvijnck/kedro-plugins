"""Kedro-as-a-service: expose the project over HTTP via Kedro's built-in server.

    uv run uvicorn feast_kedro_pipelines.service:app --host 0.0.0.0 --port 8000

See https://kedro.org/blog/kedro-as-a-service.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException
from pydantic import BaseModel, Field

from kedro.framework.session.service_session import KedroServiceSession
from kedro.io.core import generate_timestamp
from kedro.pipeline import Pipeline
from kedro.runner import SequentialRunner
from kedro.server import create_http_server

from feast_kedro_pipelines.entities import KEY_COLUMNS
from feast_kedro_pipelines.pipelines import feature_a, feature_b, filtering

# Kedro project root (…/pipelines/src/feast_kedro_pipelines/service.py -> pipelines/).
PROJECT_PATH = Path(__file__).resolve().parents[2]

app = create_http_server(project_path=str(PROJECT_PATH))

# Final (in-memory) output the last filter writes and the endpoint reads back.
SURVIVORS = "survivors"
# Maps a filter's `feature` key to that feature's pipeline builder.
FEATURE_PIPELINES: dict[str, Callable[..., Pipeline]] = {
    "a": feature_a.create_pipeline,
    "b": feature_b.create_pipeline,
}


class Filter(BaseModel):
    """A single feature filter, e.g. ``{"feature": "a", "value": "foo"}``."""

    feature: str = Field(description="Feature key; one of FEATURE_PIPELINES.")
    value: Any = Field(description="Value the feature must equal to be kept.")


class FilterRequest(BaseModel):
    """Request body for ``/filter``."""

    filters: list[Filter] = Field(
        ..., min_length=1, description="Filters applied in order, narrowing candidates."
    )
    input_dataset: str = Field(
        description="Catalog dataset the candidate pairs are read from.",
    )


class FilterResponse(BaseModel):
    """Result of a ``/filter`` invocation (one chained pipeline run)."""

    status: str = Field(description="'success' or 'failure'.")
    run_id: str = Field(description="Identifier of the pipeline run.")
    duration_ms: float = Field(description="Execution time in milliseconds.")
    remaining: list[dict] = Field(
        default_factory=list, description="Surviving drug/disease pairs."
    )
    error: dict | None = Field(default=None, description="Error details on failure.")


def _get_session() -> KedroServiceSession:
    """Return the shared service session, creating it on first use."""
    with app.state.session_lock:
        if not hasattr(app.state, "session"):
            app.state.session = KedroServiceSession.create(
                project_path=app.state.project_path,
                env=app.state.default_env,
                conf_source=app.state.default_conf_source,
            )
        return app.state.session


# Exposes the main filtering endpoint, idea is that it dymically builds
# A filter pipeline by overriding the default pipeline builders with the filters.
@app.post("/filter", response_model=FilterResponse, tags=["pipeline"])
def run_filter(request: FilterRequest) -> FilterResponse:
    """Compose a chained pipeline from the filters and run it in a single pass."""
    for f in request.filters:
        if f.feature not in FEATURE_PIPELINES:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown feature '{f.feature}'. Known: {sorted(FEATURE_PIPELINES)}.",
            )

    # Chain the existing feature/filter pipeline builders: each filter's
    # survivors are the next feature step's input dataset.
    pipe = Pipeline([])
    current = request.input_dataset
    last = len(request.filters) - 1
    for i, f in enumerate(request.filters):
        pairs = f"pairs_{i}"

        # NOTE: If you want to store this you can turn it into a factory dataset
        survivors = SURVIVORS if i == last else f"survivors_{i}"
        pipe += FEATURE_PIPELINES[f.feature](input_dataset=current, featured=pairs, step=i)
        pipe += filtering.create_pipeline(
            input_dataset=pairs, output_dataset=survivors, filters=[f.model_dump()], step=i
        )
        current = survivors

    session = _get_session()
    catalog = session.load_context().catalog
    run_id = generate_timestamp()
    start = time.perf_counter()
    try:
        outputs = SequentialRunner().run(pipe, catalog, run_id=run_id)
        remaining = outputs[SURVIVORS].load()[KEY_COLUMNS].to_dict(orient="records")
        status, error = "success", None
    except Exception as exc:
        remaining, status = [], "failure"
        error = {"type": type(exc).__qualname__, "message": str(exc)}

    return FilterResponse(
        status=status,
        run_id=run_id,
        duration_ms=round((time.perf_counter() - start) * 1000, 2),
        remaining=remaining,
        error=error,
    )
