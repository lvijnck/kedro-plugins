"""Nodes for the feature_a pipeline."""

import pandas as pd

from feast_kedro_pipelines.entities import KEY_COLUMNS


def create_feature_a(candidates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute feature A for the candidate pairs and write it to `feature_a_view`.

    Returns the feature rows (persisted to Feast) plus the candidate pairs passed
    through unchanged, so a downstream filter can depend on this node (ensuring
    the feature is written before it is read back).
    """
    pairs = candidates[KEY_COLUMNS].reset_index(drop=True)
    features = pairs.copy()
    features["feature_a"] = ["foo" if i % 2 == 0 else "bar" for i in range(len(features))]
    features["event_timestamp"] = pd.Timestamp.now(tz="UTC")
    return features, pairs
