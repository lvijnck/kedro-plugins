"""Kedro-as-a-service: expose the project over HTTP via Kedro's built-in server.

    uv run uvicorn feast_kedro_pipelines.service:app --host 0.0.0.0 --port 8000

`create_http_server` provides `/health`, `/snapshot` and `/run`. Trigger the
inference pipeline by POSTing a run request (``params`` are runtime parameters):

    curl -X POST localhost:8000/run \
        -H 'content-type: application/json' \
        -d '{"pipeline_names": ["inference"], "params": {"drug_kg_node_id": "DRUGBANK:DB00619", "disease_kg_node_id": "MONDO:0005148"}}'

See https://kedro.org/blog/kedro-as-a-service.
"""

from pathlib import Path

from kedro.server import create_http_server

# Kedro project root (…/pipelines/src/feast_kedro_pipelines/service.py -> pipelines/).
PROJECT_PATH = Path(__file__).resolve().parents[2]

app = create_http_server(project_path=str(PROJECT_PATH))
