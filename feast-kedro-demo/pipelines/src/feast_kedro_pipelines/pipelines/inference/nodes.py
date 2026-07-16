"""Nodes for the inference pipeline."""

import pandas as pd

from kedro_datasets_experimental.feast.feast_dataset import FeastFeatureSource


def predict_repurposing_score(
    drug_features: FeastFeatureSource,
    drug_kg_node_id: str,
    disease_kg_node_id: str,
) -> pd.DataFrame:
    """Score a drug-disease repurposing candidate.

    Reads the drug's latest features from Feast's **online** store and applies a
    toy model. The result is written to the offline ``repurposing_scores``
    dataset by the catalog.
    """

    # NOTE: Dataset gives you the ability to specify for which entities features should be retrieved, showing
    # use of `get_online_features`` here, but would expect users to use `get_historical_features` in a Kedro context.
    features = drug_features.get_online_features(
        pd.DataFrame({"drug_kg_node_id": [drug_kg_node_id]})
    )
    degree = features["degree"].iloc[0]
    degree = 0 if pd.isna(degree) else int(degree)
    is_steroid = features["is_steroid"].iloc[0]
    is_steroid = bool(is_steroid) if not pd.isna(is_steroid) else False

    # Toy score: better-connected, non-steroid drugs score higher.
    score = min(1.0, degree / 500.0) * (0.5 if is_steroid else 1.0)

    return pd.DataFrame(
        {
            "drug_kg_node_id": [drug_kg_node_id],
            "disease_kg_node_id": [disease_kg_node_id],
            "repurposing_score": [round(score, 4)],
            "event_timestamp": [pd.Timestamp.now(tz="UTC")],
        }
    )
