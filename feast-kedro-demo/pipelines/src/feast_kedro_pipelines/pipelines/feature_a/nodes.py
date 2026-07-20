"""Nodes for the feature_a pipeline."""

import pandas as pd


def create_feature_a() -> pd.DataFrame:
    """Insert feature A values for a few drug/disease pairs into `feature_a_view`.

    Columns match the feature view schema (drug + disease entity keys, the
    ``feature_a`` feature) plus the required ``event_timestamp``.
    """
    now = pd.Timestamp.now(tz="UTC")
    return pd.DataFrame(
        {
            "drug_kg_node_id": [
                "DRUGBANK:DB00945",  # acetylsalicylic acid (aspirin)
                "DRUGBANK:DB00619",  # imatinib
                "DRUGBANK:DB01234",  # dexamethasone
            ],
            "disease_kg_node_id": [
                "MONDO:0005148",  # type 2 diabetes mellitus
                "MONDO:0005148",
                "MONDO:0005148",
            ],
            "feature_a": ["foo", "bar", "foo"],
            "event_timestamp": [now] * 3,
        }
    )
