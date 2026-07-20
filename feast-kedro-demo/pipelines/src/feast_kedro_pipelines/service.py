"""Kedro-as-a-service: expose the project over HTTP via Kedro's built-in server.

    uv run uvicorn feast_kedro_pipelines.service:app --host 0.0.0.0 --port 8000

`create_http_server` provides `/health`, `/snapshot` and `/run`. Trigger the
inference pipeline by POSTing a run request (``params`` are runtime parameters):

    curl -X POST localhost:8000/run \
        -H 'content-type: application/json' \
        -d '{"pipeline_names": ["inference"], "params": {"drug_kg_node_id": "DRUGBANK:DB00619", "disease_kg_node_id": "MONDO:0005148"}}'

On top of the built-in routes this module adds ``/filter``. Callers don't pass
pipeline names — they pass a list of feature filters. The endpoint runs the
feature pipeline(s) needed to compute the referenced features first, then runs
the ``filtering`` pipeline (which reads the feature service and applies the
filters):

    curl -X POST localhost:8000/filter \
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
from kedro.server.models import RunRequest, RunResponse
from kedro.server.http_server import _execute_pipeline

# Kedro project root (…/pipelines/src/feast_kedro_pipelines/service.py -> pipelines/).
PROJECT_PATH = Path(__file__).resolve().parents[2]

app = create_http_server(project_path=str(PROJECT_PATH))

# Maps a filter's ``feature`` key to the pipeline that computes and writes it
# to Feast. Extend this as new feature pipelines/views are added.
FEATURE_PIPELINES: dict[str, str] = {
    "a": "feature_a",
    "b": "feature_b",
}
# Pipeline that reads the feature service and applies the filters.
FILTER_PIPELINE = "filtering"


class Filter(BaseModel):
    """A single feature filter, e.g. ``{"feature": "a", "value": "foo"}``."""

    feature: str = Field(description="Feature key; one of FEATURE_PIPELINES.")
    value: Any = Field(description="Value the feature must equal to be kept.")


class FilterRequest(BaseModel):
    """Request body for the ``/filter`` endpoint."""

    filters: list[Filter] = Field(
        ...,
        min_length=1,
        description="Feature filters to apply; AND-ed together.",
    )


class FilterResponse(BaseModel):
    """Aggregated result of a ``/filter`` invocation."""

    status: str = Field(description="'success' if every run succeeded, else 'failure'.")
    pipelines: list[str] = Field(
        description="Pipelines executed, in order (feature pipelines then filtering)."
    )
    results: list[RunResponse] = Field(
        description="Per-pipeline run results, in execution order."
    )


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


@app.post("/filter", response_model=FilterResponse, tags=["pipeline"])
def run_filter(request: FilterRequest) -> FilterResponse:
    """Compute the features referenced by the filters, then filter drugs.

    The feature pipeline for each referenced feature is run first (deduplicated,
    in first-seen order) so the features are freshly written to Feast, then the
    ``filtering`` pipeline runs with the filters passed as a runtime parameter.
    Execution stops at the first failing run and returns the partial results.
    """
    # Resolve which feature pipelines to run, preserving first-seen order and
    # rejecting unknown features up front (before running anything).
    feature_pipelines: list[str] = []
    for f in request.filters:
        pipeline_name = FEATURE_PIPELINES.get(f.feature)
        if pipeline_name is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Unknown feature '{f.feature}'. "
                    f"Known features: {sorted(FEATURE_PIPELINES)}."
                ),
            )
        if pipeline_name not in feature_pipelines:
            feature_pipelines.append(pipeline_name)

    session = _get_session()
    executed: list[str] = []
    results: list[RunResponse] = []

    def _run(name: str, params: dict[str, Any] | None = None) -> bool:
        result = _execute_pipeline(
            session=session,
            request=RunRequest(pipeline_names=[name], params=params),
        )
        executed.append(name)
        results.append(result)
        return result.status == "success"

    # 1. Compute features. 2. Filter, passing the filters as a runtime param.
    for name in feature_pipelines:
        if not _run(name):
            return FilterResponse(status="failure", pipelines=executed, results=results)

    filters_param = [f.model_dump() for f in request.filters]
    ok = _run(FILTER_PIPELINE, params={"filters": filters_param})

    return FilterResponse(
        status="success" if ok else "failure",
        pipelines=executed,
        results=results,
    )
