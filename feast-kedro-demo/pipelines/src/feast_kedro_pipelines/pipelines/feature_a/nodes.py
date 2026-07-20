"""Nodes for the feature_a pipeline."""

import pandas as pd

_KEY_COLUMNS = ["drug_kg_node_id", "disease_kg_node_id"]


def create_feature_a(candidates: pd.DataFrame) -> pd.DataFrame:
    """Insert feature A values for the current candidate pairs into `feature_a_view`.

    ``candidates`` is read from the working-set catalog dataset (the pairs that
    survive so far). Feature values are a toy deterministic assignment; the
    returned frame is written to Feast.
    """
    df = candidates[_KEY_COLUMNS].reset_index(drop=True)
    df["feature_a"] = ["foo" if i % 2 == 0 else "bar" for i in range(len(df))]
    df["event_timestamp"] = pd.Timestamp.now(tz="UTC")
    return df
