"""Feast feature definitions for a drug-repurposing feature store.

Mirrors the domain from "Building a feature store with Kedro and Feast":
biomedical knowledge-graph features for drugs and diseases.

- ``drug_feature_view``: written offline by the feature-engineering pipeline,
  then pushed to the online store by ``feast materialize-incremental``.
- ``repurposing_scores``: written offline + online directly by the inference
  pipeline (not materialized), so applications can read scores online.
- ``application_feature_service``: bundles the drug features for app serving.
"""

import os
from datetime import timedelta

from feast import BigQuerySource, Entity, FeatureService, FeatureView, Field, ValueType
from feast.types import Bool, Float64, Int64, String

GCP_PROJECT = os.environ.get("GCP_PROJECT", "your-gcp-project")
BQ_DATASET = os.environ.get("BQ_DATASET", "feast")

# Give the entities an explicit `value_type`. Without it Feast strips the
# join-key fields from the view schema and has to read the source table during
# `feast apply` to infer their type -- which fails (404) before the ingest
# pipeline has created the tables.
drug = Entity(name="drug", join_keys=["drug_kg_node_id"], value_type=ValueType.STRING)
disease = Entity(
    name="disease", join_keys=["disease_kg_node_id"], value_type=ValueType.STRING
)

# Knowledge-graph features for a drug node.
drug_features_source = BigQuerySource(
    table=f"{GCP_PROJECT}.{BQ_DATASET}.drug_features",
    timestamp_field="event_timestamp",
)

drug_feature_view = FeatureView(
    name="drug_feature_view",
    entities=[drug],
    ttl=timedelta(days=3650),
    online=True,
    schema=[
        Field(name="name", dtype=String),
        Field(name="is_steroid", dtype=Bool),
        Field(name="degree", dtype=Int64),  # knowledge-graph node degree
    ],
    source=drug_features_source,
)

# Offline-only sink for inference results: drug-disease repurposing scores.
repurposing_scores_source = BigQuerySource(
    table=f"{GCP_PROJECT}.{BQ_DATASET}.repurposing_scores",
    timestamp_field="event_timestamp",
)

repurposing_scores_fv = FeatureView(
    name="repurposing_scores",
    entities=[drug, disease],
    ttl=timedelta(days=3650),
    online=True,
    schema=[
        Field(name="repurposing_score", dtype=Float64),
    ],
    source=repurposing_scores_source,
)
