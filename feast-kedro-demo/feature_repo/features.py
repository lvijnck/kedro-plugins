"""Feast feature definitions: a driver-stats feature view backed by BigQuery."""

import os
from datetime import timedelta

from feast import BigQuerySource, Entity, FeatureView, Field
from feast.types import Float64, Int64

GCP_PROJECT = os.environ.get("GCP_PROJECT", "your-gcp-project")
BQ_DATASET = os.environ.get("BQ_DATASET", "feast_kedro_demo")

driver = Entity(name="driver", join_keys=["driver_id"])

# The offline (batch) source. `FeastDataset(create_table=True)` bootstraps this
# table from the feature view schema below; the BQ *dataset* must already exist.
driver_stats_source = BigQuerySource(
    table=f"{GCP_PROJECT}.{BQ_DATASET}.driver_stats",
    timestamp_field="event_timestamp",
)

driver_stats_fv = FeatureView(
    name="driver_stats",
    entities=[driver],
    ttl=timedelta(days=3650),
    online=True,
    schema=[
        Field(name="driver_id", dtype=Int64),
        Field(name="trips", dtype=Int64),
        Field(name="rating", dtype=Float64),
    ],
    source=driver_stats_source,
)

# Offline-only sink for inference results (expected trip prices).
predicted_trip_prices_source = BigQuerySource(
    table=f"{GCP_PROJECT}.{BQ_DATASET}.predicted_trip_prices",
    timestamp_field="event_timestamp",
)

predicted_trip_prices_fv = FeatureView(
    name="predicted_trip_prices",
    entities=[driver],
    ttl=timedelta(days=3650),
    online=False,
    schema=[
        Field(name="driver_id", dtype=Int64),
        Field(name="distance", dtype=Float64),
        Field(name="predicted_trip_price", dtype=Float64),
    ],
    source=predicted_trip_prices_source,
)
