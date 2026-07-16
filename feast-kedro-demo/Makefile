.PHONY: venv up apply features materialize serve run-inference down

ifeq ($(wildcard .env),)

$(error Missing .env file. Copy .env.example to .env and configure it.)

endif

# `-include` so a missing .env is fine in the container (env comes from compose).
-include .env
export

# Default the registry to a local path, but let the environment (docker-compose
# sets FEAST_REGISTRY=/registry) win.
FEAST_REGISTRY ?= $(CURDIR)/features/data/registry.db
export FEAST_REGISTRY

# Sync ALL workspace members (pipelines + services) into one venv. The root is
# a virtual (package=false) workspace, so --all-packages is required to install
# the members' dependencies (feast, kedro, ...).
venv:
	uv sync --all-packages

# Spin up the whole stack in docker (postgres -> apply -> features -> inference).
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
	uv run --no-sync feast --chdir features apply --skip-source-validation --skip-feature-view-validation

# Run the feature-engineering pipeline (writes drug features to BigQuery + Postgres).
features:
	cd pipelines && uv run --no-sync kedro run

# Push the drug features from the offline store into the online store (till EOD).
materialize:
	uv run --no-sync feast --chdir features materialize-incremental \
		"$$(date -u +%Y-%m-%dT23:59:59)"

# Serve the project over HTTP (Kedro's built-in create_http_server).
serve:
	cd pipelines && uv run --no-sync uvicorn feast_kedro_pipelines.service:app --host 0.0.0.0 --port 8000

feast-ui:
	uv run --no-sync feast --chdir features ui

# Trigger the inference pipeline over HTTP and store results in the online store.
run-inference:
	curl -X POST localhost:8000/run -H 'content-type: application/json' \
		-d '{"pipeline_names":["inference"],"params":{"drug_kg_node_id":"DRUGBANK:DB00945","disease_kg_node_id":"MONDO:0005120"}}'
