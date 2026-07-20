"""Nodes for the feature_b pipeline."""

import pandas as pd

_KEY_COLUMNS = ["drug_kg_node_id", "disease_kg_node_id"]


def create_feature_b(candidates: pd.DataFrame) -> pd.DataFrame:
    """Insert feature B values for the current candidate pairs into `feature_b_view`.

    ``candidates`` is read from the working-set catalog dataset (the pairs that
    survive so far). Feature values are a toy deterministic assignment; the
    returned frame is written to Feast.
    """
    df = candidates[_KEY_COLUMNS].reset_index(drop=True)
    df["feature_b"] = ["high" if i % 2 == 0 else "low" for i in range(len(df))]
    df["event_timestamp"] = pd.Timestamp.now(tz="UTC")
    return df
