.PHONY: venv up apply ingest serve run-inference down

include .env
export

# Local runs share one registry file with the docker stack's semantics.
FEAST_REGISTRY := $(CURDIR)/features/data/registry.db
export FEAST_REGISTRY

# Sync ALL workspace members (pipelines + services) into one venv. The root is
# a virtual (package=false) workspace, so --all-packages is required to install
# the members' dependencies (feast, kedro, ...).
venv:
	uv sync --all-packages

# Spin up the whole stack in docker (postgres -> apply -> ingest -> inference).
up:
	docker compose up -d --build

down:
	docker compose down

# --- local (non-docker) targets; run `make venv` first -------------------- #
# `uv run --no-sync` uses the already-synced workspace venv as-is (so it isn't
# re-synced down to the empty virtual root).

# Register the feature repo (writes the registry, creates the Postgres tables).
apply:
	mkdir -p features/data
	uv run --no-sync feast --chdir features apply --skip-source-validation

# Run the ingestion pipeline (writes features to BigQuery + Postgres).
ingest:
	cd pipelines && uv run --no-sync kedro run --pipeline feature_ingestion

# Serve the project over HTTP (Kedro's built-in create_http_server).
serve:
	cd pipelines && uv run --no-sync uvicorn feast_kedro_pipelines.service:app --host 0.0.0.0 --port 8000

# Trigger the inference pipeline over HTTP (server must be running).
run-inference:
	curl -X POST localhost:8000/run -H 'content-type: application/json' \
		-d '{"pipeline_names":["inference"],"params":{"driver_id":1001,"distance":12.5}}'
