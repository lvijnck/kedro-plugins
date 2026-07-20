"""Kedro-as-a-service: expose the project over HTTP via Kedro's built-in server.

    uv run uvicorn feast_kedro_pipelines.service:app --host 0.0.0.0 --port 8000

`create_http_server` provides `/health`, `/snapshot` and `/run`. Trigger the
inference pipeline by POSTing a run request (``params`` are runtime parameters):

    curl -X POST localhost:8000/run \
        -H 'content-type: application/json' \
        -d '{"pipeline_names": ["inference"], "params": {"drug_kg_node_id": "DRUGBANK:DB00619", "disease_kg_node_id": "MONDO:0005148"}}'

On top of the built-in routes this module adds ``/filter-iterative``. The
candidate drug/disease pairs are seeded from the ``candidates`` catalog dataset
(``data/candidates.csv``) and flow between runs through the catalog; callers only
pass feature filters (never entities or pipeline names). For each filter in turn
it computes that feature for the *current* candidates, applies the filter, and
writes the survivors back through the catalog, so later features are only
computed for what is left:

    curl -X POST localhost:8000/filter-iterative \
        -H 'content-type: application/json' \
        -d '{"filters": [{"feature": "a", "value": "foo"}, {"feature": "b", "value": "high"}]}'

See https://kedro.org/blog/kedro-as-a-service.
"""

from pathlib import Path
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field

from kedro.framework.session.service_session import KedroServiceSession
from kedro.server import create_http_server
from kedro.server.http_server import _execute_pipeline
from kedro.server.models import RunRequest, RunResponse

# Kedro project root (…/pipelines/src/feast_kedro_pipelines/service.py -> pipelines/).
PROJECT_PATH = Path(__file__).resolve().parents[2]

app = create_http_server(project_path=str(PROJECT_PATH))

# Maps a filter's ``feature`` key to the pipeline that computes and writes it
# to Feast. Extend this as new feature pipelines/views are added.
FEATURE_PIPELINES: dict[str, str] = {
    "a": "feature_a",
    "b": "feature_b",
}
# Copies the candidate seed into the working set (run once per request).
PRIME_PIPELINE = "prime"
# Reads the feature service + working set, applies filters, writes survivors.
FILTER_PIPELINE = "filtering"
# Working-set catalog dataset (read handle), inspected only to report survivors.
_WORKING_DATASET = "input"
_KEY_COLUMNS = ["drug_kg_node_id", "disease_kg_node_id"]


class Filter(BaseModel):
    """A single feature filter, e.g. ``{"feature": "a", "value": "foo"}``."""

    feature: str = Field(description="Feature key; one of FEATURE_PIPELINES.")
    value: Any = Field(description="Value the feature must equal to be kept.")


class FilterRequest(BaseModel):
    """Request body shared by ``/filter`` and ``/filter-iterative``."""

    filters: list[Filter] = Field(
        ...,
        min_length=1,
        description="Feature filters to apply; AND-ed together.",
    )


class IterativeStep(BaseModel):
    """One filter's iteration: compute the feature, then apply the filter."""

    filter: dict = Field(description="The filter applied in this iteration.")
    feature_run: RunResponse = Field(description="Result of the feature pipeline run.")
    filter_run: RunResponse | None = Field(
        default=None, description="Result of the filtering run (absent if feature run failed)."
    )
    remaining: int = Field(description="Candidate pairs remaining after this step.")


class IterativeResponse(BaseModel):
    """Aggregated result of a ``/filter-iterative`` invocation."""

    status: str = Field(description="'success' if every run succeeded, else 'failure'.")
    steps: list[IterativeStep] = Field(description="Per-filter iterations, in order.")
    remaining: list[dict] = Field(description="Final surviving drug/disease pairs.")


def _get_session() -> KedroServiceSession:
    """Return the shared service session, creating it on first use.

    Mirrors the lazy, single-session behaviour of the built-in ``/run`` route so
    both endpoints reuse the same bootstrapped session.
    """
    with app.state.session_lock:
        if not hasattr(app.state, "session"):
            app.state.session = KedroServiceSession.create(
                project_path=app.state.project_path,
                env=app.state.default_env,
                conf_source=app.state.default_conf_source,
            )
        return app.state.session


def _run(
    session: KedroServiceSession,
    name: str,
    params: dict[str, Any] | None = None,
) -> RunResponse:
    """Run a single pipeline and return its structured result."""
    return _execute_pipeline(
        session=session,
        request=RunRequest(pipeline_names=[name], params=params),
    )


def _read_working(session: KedroServiceSession) -> list[dict]:
    """Read the working-set catalog dataset (survivors) for the response.

    This inspects the result the pipelines wrote through the catalog; the
    candidate set itself is passed run-to-run via the catalog, never in memory.
    """
    catalog = session.load_context().catalog
    df = catalog[_WORKING_DATASET].load()
    return df[_KEY_COLUMNS].to_dict(orient="records")


def _validate_features(filters: list[Filter]) -> None:
    """Reject filters referencing unknown features before running anything."""
    for f in filters:
        if f.feature not in FEATURE_PIPELINES:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Unknown feature '{f.feature}'. "
                    f"Known features: {sorted(FEATURE_PIPELINES)}."
                ),
            )


def _prime(session: KedroServiceSession) -> None:
    """Reset the working set from the seed; raise 500 if it fails."""
    result = _run(session, PRIME_PIPELINE)
    if result.status == "failure":
        raise HTTPException(
            status_code=500,
            detail={"stage": PRIME_PIPELINE, "error": result.error.model_dump()},
        )


@app.post("/filter-iterative", response_model=IterativeResponse, tags=["pipeline"])
def run_filter_iterative(request: FilterRequest) -> IterativeResponse:
    """Apply the filters one at a time, narrowing the working set each step.

    Seeds the working set (``prime``), then for each filter in order: run its
    feature pipeline over the current working candidates, then run ``filtering``
    with just that filter — which writes the survivors back through the catalog.
    The next feature pipeline reads that narrowed set, so later features are only
    computed for what remains. Stops at the first failure, or early once empty.
    """
    _validate_features(request.filters)

    session = _get_session()
    _prime(session)
    steps: list[IterativeStep] = []

    for f in request.filters:
        filter_param = f.model_dump()

        # 1. Compute this feature for the current working candidates.
        feature_run = _run(session, FEATURE_PIPELINES[f.feature])
        if feature_run.status == "failure":
            steps.append(
                IterativeStep(
                    filter=filter_param,
                    feature_run=feature_run,
                    remaining=len(_read_working(session)),
                )
            )
            return IterativeResponse(
                status="failure", steps=steps, remaining=_read_working(session)
            )

        # 2. Apply this single filter; survivors are written back via the catalog.
        filter_run = _run(session, FILTER_PIPELINE, {"filters": [filter_param]})
        remaining = _read_working(session)
        steps.append(
            IterativeStep(
                filter=filter_param,
                feature_run=feature_run,
                filter_run=filter_run,
                remaining=len(remaining),
            )
        )
        if filter_run.status == "failure":
            return IterativeResponse(status="failure", steps=steps, remaining=remaining)
        if not remaining:
            break  # nothing survives; no point computing further features

    return IterativeResponse(
        status="success", steps=steps, remaining=_read_working(session)
    )
