"""Nodes for the filtering pipeline."""

import pandas as pd

from kedro_datasets_experimental.feast.feast_dataset import FeastFeatureSource

_KEY_COLUMNS = ["drug_kg_node_id", "disease_kg_node_id"]


def filter_drugs(
    filter_features: FeastFeatureSource,
    candidates: pd.DataFrame,
    filters: list[dict],
) -> pd.DataFrame:
    """Keep the candidate pairs whose feature values match every filter.

    Reads features for the current ``candidates`` (from the working-set catalog
    dataset) via a point-in-time join, applies each filter
    ``{"feature": "a", "value": "foo"}`` as ``feature_a == "foo"`` (AND-ed), and
    returns the surviving pairs. The result is written back through the catalog
    (``iterative_output``), narrowing the working set for the next run.
    """
    survivors = candidates[_KEY_COLUMNS].reset_index(drop=True)
    if survivors.empty:
        return survivors

    entity_df = survivors.copy()
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

    survivors = df[_KEY_COLUMNS].reset_index(drop=True)
    print(survivors.to_string(index=False))
    return survivors
