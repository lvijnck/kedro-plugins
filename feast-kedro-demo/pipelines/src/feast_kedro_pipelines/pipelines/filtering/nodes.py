"""Nodes for the filtering pipeline."""

import pandas as pd

from kedro_datasets_experimental.feast.feast_dataset import FeastFeatureSource

from feast_kedro_pipelines.entities import KEY_COLUMNS


def filter_drugs(
    filter_features: FeastFeatureSource,
    candidates: pd.DataFrame,
    filters: list[dict],
) -> pd.DataFrame:
    """Keep the candidate pairs whose feature values match every filter.

    Retrieves features for ``candidates`` from the feature service via a
    point-in-time join, then applies each ``{"feature": "a", "value": "foo"}``
    as ``feature_a == "foo"`` (AND-ed). Returns the surviving pairs.
    """
    pairs = candidates[KEY_COLUMNS].reset_index(drop=True)
    if pairs.empty:
        return pairs

    entity_df = pairs.copy()
    entity_df["event_timestamp"] = pd.Timestamp.now(tz="UTC")
    df = filter_features.get_historical_features(entity_df=entity_df)

    for f in (dict(x) for x in filters):
        column = f"feature_{f['feature']}"
        if column not in df.columns:
            raise ValueError(
                f"Filter references unknown feature '{f['feature']}' "
                f"(column '{column}' not in {list(df.columns)})."
            )
        df = df[df[column] == f["value"]]

    return df[KEY_COLUMNS].reset_index(drop=True)
