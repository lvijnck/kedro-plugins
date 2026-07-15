# feast-kedro-demo

A demo of the experimental **`FeastDataset`** (from the sibling
`../kedro-datasets`), organised as:

```
feast-kedro-demo/
├── features/     # Feast repo: feature_store.yaml + features.py (feature views)
└── pipelines/    # Kedro project: feature_ingestion + inference pipelines
```

- **features/** — offline store: BigQuery; online store: Postgres. Two feature
  views: `driver_stats` (online + offline) and `predicted_trip_prices`
  (offline only, written by inference).
- **pipelines/** — a Kedro project with two pipelines, both using `FeastDataset`:
  - `feature_ingestion` — writes dummy `driver_stats` to both stores
    (`write_mode: online_and_offline`, `create_table: true`).
  - `inference` — reads a driver's **online** features, predicts an expected
    trip price, and writes it to the offline-only `predicted_trip_prices`.
  - It is exposed over HTTP via Kedro's built-in server
    (`kedro.server.create_http_server`) — "Kedro as a service".

## Prerequisites

- Python ≥ 3.10, [`uv`](https://docs.astral.sh/uv/), Docker, `gcloud`/`bq`.
- A GCP project with a BigQuery **dataset** that already exists (tables are
  created for you; the dataset is not).

## Run everything in Docker

```bash
cp .env.example .env          # edit GCP_PROJECT / BQ_DATASET
gcloud auth application-default login
bq --location=US mk -d "$GCP_PROJECT:$BQ_DATASET"   # if it doesn't exist

make up                        # postgres -> apply -> ingest -> inference server (:8000)
make run-inference             # POST /run for the inference pipeline
```

`apply` and `ingest` are one-shot jobs; `inference` (the Kedro HTTP server)
starts only after they complete. The Feast registry is shared through a named
volume.

## Run locally (no Docker for the app)

```bash
make venv                      # uv sync --all-packages (workspace -> one venv)
docker compose up -d postgres  # online store only
cp .env.example .env && set -a && source .env && set +a

make apply                     # feast apply (features/)
make ingest                    # kedro run feature_ingestion
make serve                     # kedro HTTP server (create_http_server) on :8000
make run-inference             # in another shell: POST /run
```

`POST /run` accepts a Kedro run request; `params` are runtime parameters:

```bash
curl -X POST localhost:8000/run -H 'content-type: application/json' \
  -d '{"pipeline_names":["inference"],"params":{"driver_id":1002,"distance":20.0}}'
```

## Verify

```bash
bq query --use_legacy_sql=false \
  "SELECT * FROM \`$GCP_PROJECT.$BQ_DATASET.driver_stats\` ORDER BY driver_id"
bq query --use_legacy_sql=false \
  "SELECT * FROM \`$GCP_PROJECT.$BQ_DATASET.predicted_trip_prices\`"
```

## Notes

- The `repo` blocks in `pipelines/conf/base/catalog.yml` and
  `features/feature_store.yaml` describe the same Feast stores (registry,
  project, offline/online, `entity_key_serialization_version: 3`). Keep them in sync.
- `FEAST_REGISTRY` points every component at one registry file: the `Makefile`
  sets it to `features/data/registry.db` for local runs; docker-compose sets it
  to a shared `/registry` volume.
- `FeastDataset` authenticates to BigQuery via Application Default Credentials
  (no `credentials` argument).
