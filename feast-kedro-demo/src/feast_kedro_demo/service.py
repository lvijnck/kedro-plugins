"""Kedro-as-a-service: expose the inference pipeline over HTTP.

Run with:

    uv run uvicorn feast_kedro_demo.service:app --reload

Then:

    curl -X POST localhost:8000/predict \
        -H 'content-type: application/json' \
        -d '{"driver_id": 1001, "distance": 12.5}'

The pipeline persists its result to the offline store (BigQuery); the endpoint
just triggers the run. See https://kedro.org/blog/kedro-as-a-service.
"""

from pathlib import Path

from fastapi import FastAPI
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from pydantic import BaseModel

# Project root (…/src/feast_kedro_demo/service.py -> project root).
PROJECT_PATH = Path(__file__).resolve().parents[2]

# Bootstrap the Kedro project once, at import time.
bootstrap_project(PROJECT_PATH)

app = FastAPI(title="feast-kedro-demo inference")


class PredictRequest(BaseModel):
    driver_id: int
    distance: float


@app.post("/predict")
def predict(request: PredictRequest) -> dict:
    """Run the ``inference`` pipeline for one driver/distance.

    Each request runs the pipeline in a fresh ``KedroSession`` with the driver
    id and distance injected as runtime parameters. The prediction is written
    to the offline store by the pipeline (not returned here).
    """
    with KedroSession.create(
        project_path=PROJECT_PATH,
        runtime_params={"driver_id": request.driver_id, "distance": request.distance},
    ) as session:
        session.run(pipeline_name="inference")

    return {
        "status": "ok",
        "session_id": session.session_id,
        "driver_id": request.driver_id,
        "distance": request.distance,
    }
