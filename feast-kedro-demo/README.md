# feast-kedro-demo

A drug-repurposing feature store built with Kedro + Feast, using the
experimental **`FeastDataset`** (from the sibling `../kedro-datasets`). It
follows the theme of
[Building a feature store with Kedro and Feast](https://kedro.org/blog/building-a-feature-store-with-kedro-and-feast):
biomedical knowledge-graph features serving both offline analytics and online
applications.

```
feast-kedro-demo/
├── features/     # Feast repo: feature_store.yaml + features.py (feature views)
└── pipelines/    # Kedro project: feature_engineering + inference pipelines
```

- **features/** — offline store: BigQuery; online store: Postgres.
  - `drug_feature_view` (entity `drug` / `drug_kg_node_id`): `name`,
    `is_steroid`, `degree` — online + offline.
  - `repurposing_scores` (offline only): drug-disease scores written by inference.
  - `application_feature_service` bundles the drug features for online serving.
- **pipelines/** — a Kedro project with two pipelines, both using `FeastDataset`:
  - `feature_engineering` — computes drug features and writes them to both
    stores (`write_mode: online_and_offline`, `create_table: true`).
  - `inference` — reads a drug's **online** features, scores a drug-disease
    repurposing candidate, and writes it to the offline-only `repurposing_scores`.
  - Exposed over HTTP via Kedro's built-in server
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

make up                        # postgres -> apply -> features -> inference server (:8000)
make run-inference             # POST /run for the inference pipeline
```

`apply` and `features` are one-shot jobs; `inference` (the Kedro HTTP server)
starts only after they complete. The Feast registry is shared through a named
volume.

## Run locally (no Docker for the app)

```bash
make venv                      # uv sync --all-packages (workspace -> one venv)
docker compose up -d postgres  # online store only
cp .env.example .env && set -a && source .env && set +a

make apply                     # feast apply (features/)
make features                  # kedro run feature_engineering
make serve                     # kedro HTTP server (create_http_server) on :8000
make run-inference             # in another shell: POST /run
```

`POST /run` accepts a Kedro run request; `params` are runtime parameters:

```bash
curl -X POST localhost:8000/run -H 'content-type: application/json' \
  -d '{"pipeline_names":["inference"],
       "params":{"drug_kg_node_id":"DRUGBANK:DB00619","disease_kg_node_id":"MONDO:0005148"}}'
```

## Verify

```bash
bq query --use_legacy_sql=false \
  "SELECT * FROM \`$GCP_PROJECT.$BQ_DATASET.drug_features\` ORDER BY drug_kg_node_id"
bq query --use_legacy_sql=false \
  "SELECT * FROM \`$GCP_PROJECT.$BQ_DATASET.repurposing_scores\`"
```

## Notes

- The `repo` blocks in `pipelines/conf/base/catalog.yml` and
  `features/feature_store.yaml` describe the same Feast stores (registry,
  project `drug_repurposing`, offline/online, `entity_key_serialization_version: 3`).
  Keep them in sync.
- The online store can also be refreshed on a schedule with
  `feast materialize-incremental <timestamp>` (offline → online), as in the blog;
  here `feature_engineering` writes both stores directly for simplicity.
- `FEAST_REGISTRY` points every component at one registry file: the `Makefile`
  sets it to `features/data/registry.db` for local runs; docker-compose sets it
  to a shared `/registry` volume.
- `FeastDataset` authenticates to BigQuery via Application Default Credentials
  (no `credentials` argument).
