# feast-kedro-demo

A tiny Kedro project that exercises the experimental **`FeastDataset`** (from the
sibling `../kedro-datasets` checkout): a pipeline generates a dummy
`driver_stats` DataFrame and writes it to **both** Feast stores —

- **offline store:** BigQuery (`write_to_offline_store`, table bootstrapped from
  the feature view schema via `create_table`),
- **online store:** Postgres (from `docker-compose.yml`).

## Layout

```
feast-kedro-demo/
├── docker-compose.yml / Dockerfile   # Postgres online store
├── feature_repo/
│   ├── feature_store.yaml            # offline: bigquery, online: postgres
│   └── features.py                   # driver Entity + driver_stats FeatureView (BigQuerySource)
├── conf/base/catalog.yml             # driver_stats_features -> FeastDataset
└── src/feast_kedro_demo/             # Kedro pipeline (create dummy df -> FeastDataset)
```

## Prerequisites

- Python ≥ 3.10, [`uv`](https://docs.astral.sh/uv/), Docker, and the `gcloud`/`bq` CLIs.
- A GCP project with BigQuery, and a BigQuery **dataset** that already exists
  (the table is created for you; the dataset is not).

## Setup

```bash
cd feast-kedro-demo

# 1. Install (pulls in the local, editable kedro-datasets with FeastDataset).
uv sync

# 2. Configure env + auth.
cp .env.example .env            # edit GCP_PROJECT / BQ_DATASET
set -a; source .env; set +a
gcloud auth application-default login
bq --location=US mk -d "$GCP_PROJECT:$BQ_DATASET"   # if the dataset doesn't exist

# 3. Start the Postgres online store.
docker compose up -d            # or: docker build -t feast-online-postgres . && docker run -p 5432:5432 feast-online-postgres

# 4. Register the feature repo (creates feature_repo/data/registry.db and the
#    Postgres online tables). Uses feature_store.yaml.
cd feature_repo && uv run feast apply && cd ..
```

## Run the pipeline

```bash
uv run kedro run
```

This saves the dummy DataFrame through `FeastDataset`, which:
1. creates `"$GCP_PROJECT.$BQ_DATASET.driver_stats"` (if missing) from the
   feature view schema and appends the rows (offline store), then
2. pushes the rows to the Postgres online store.

## Verify

```bash
# Offline (BigQuery):
bq query --use_legacy_sql=false \
  "SELECT * FROM \`$GCP_PROJECT.$BQ_DATASET.driver_stats\` ORDER BY driver_id"

# Online (Feast -> Postgres):
cd feature_repo && uv run python - <<'PY'
from feast import FeatureStore
store = FeatureStore(repo_path=".")
print(store.get_online_features(
    features=["driver_stats:trips", "driver_stats:rating"],
    entity_rows=[{"driver_id": 1001}, {"driver_id": 1002}, {"driver_id": 1003}],
).to_dict())
PY
```

## Notes

- The `repo` block in `conf/base/catalog.yml` mirrors `feature_repo/feature_store.yaml`
  (same registry, project, offline/online stores, and
  `entity_key_serialization_version`). Keep them in sync — the online write must
  use the same serialization as `feast apply`.
- `FeastDataset` authenticates to BigQuery via Application Default Credentials
  (there is no `credentials` argument).
