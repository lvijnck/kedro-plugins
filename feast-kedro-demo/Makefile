.PHONY: up

include .env
export

venv:
	uv venv
	uv sync

# Spin up the Postgres instance used as Feast's online store.
up:
	docker compose up -d

# Apply the Feast feature store schema to the BigQuery and Postgres instances.
apply:
	cd feature_repo && uv run feast apply --skip-source-validation


# Run batch pipeline to ingest features into the BigQuery and Postgres instances, if the
# data already exists in BigQuery, one can run `feast materialize-incremental` to update the features.
ingest-features:
	uv run kedro run --pipeline feature_ingestion

# Run inference pipeline to predict the expected trip price for a given driver and distance.
predict-trip-price:
	uv run kedro run --pipeline inference --params inference_params.driver_id=1001,inference_params.distance=12.5

# Serve the inference pipeline over HTTP (Kedro as a service). POST /predict
# with {"driver_id": ..., "distance": ...} to trigger a run.
serve:
	uv run uvicorn feast_kedro_demo.service:app --host 0.0.0.0 --port 8000
