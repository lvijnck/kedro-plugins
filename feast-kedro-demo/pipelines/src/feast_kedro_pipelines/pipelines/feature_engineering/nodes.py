"""Nodes for the feature-engineering pipeline."""

import pandas as pd


def create_drug_features() -> pd.DataFrame:
    """Compute dummy knowledge-graph features for a few drugs.

    Columns match the ``drug_feature_view`` schema plus the required
    ``event_timestamp`` (stamped now, so the rows fall within the
    materialize-incremental window that syncs offline -> online).
    """
    now = pd.Timestamp.now(tz="UTC")
    return pd.DataFrame(
        {
            "drug_kg_node_id": [
                "DRUGBANK:DB00945",  # acetylsalicylic acid (aspirin)
                "DRUGBANK:DB00619",  # imatinib
                "DRUGBANK:DB01234",  # dexamethasone
            ],
            "name": ["acetylsalicylic acid", "imatinib", "dexamethasone"],
            "is_steroid": [False, False, True],
            "degree": [128, 342, 87],
            "event_timestamp": [now] * 3,
        }
    )
