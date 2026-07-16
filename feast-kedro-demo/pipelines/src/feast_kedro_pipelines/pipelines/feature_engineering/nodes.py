"""Nodes for the feature-engineering pipeline."""

import pandas as pd

from kedro_datasets_experimental.feast.feast_dataset import FeastFeatureSource


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


def print_drug_features(drug_features: FeastFeatureSource) -> None:
    """Fetch and print all drug features from the offline store.

    Uses timestamp-range retrieval (no entity dataframe): every feature row
    written within the window is returned, so this echoes the whole feature
    view rather than a fixed set of entities.
    """
    end = pd.Timestamp.now(tz="UTC")
    start = end - pd.Timedelta(days=3650)
    features = drug_features.get_historical_features(
        start_date=start.to_pydatetime(),
        end_date=end.to_pydatetime(),
    )
    print(features.to_string(index=False))
