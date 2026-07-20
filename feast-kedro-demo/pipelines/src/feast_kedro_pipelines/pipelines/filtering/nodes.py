"""Nodes for the filtering pipeline."""

import pandas as pd

from kedro_datasets_experimental.feast.feast_dataset import FeastFeatureSource


def filter_drugs(
    filter_features: FeastFeatureSource,
    filters: list[dict],
) -> pd.DataFrame:
    """Retrieve the bundled features and keep drugs matching every filter.

    ``filter_features`` loads from ``filter_feature_service`` (feature_a_view +
    feature_b_view), so the retrieved frame has a ``feature_a`` and a
    ``feature_b`` column. Each filter ``{"feature": "a", "value": "foo"}`` is
    applied as ``feature_a == "foo"``; filters are AND-ed together.
    """
    # Timestamp-range retrieval (no entity dataframe): return every feature row
    # written within the window, then filter client-side.
    end = pd.Timestamp.now(tz="UTC")
    start = end - pd.Timedelta(days=3650)
    df = filter_features.get_historical_features(
        start_date=start.to_pydatetime(),
        end_date=end.to_pydatetime(),
    )

    for f in filters:
        column = f"feature_{f['feature']}"
        if column not in df.columns:
            raise ValueError(
                f"Filter references unknown feature '{f['feature']}' "
                f"(column '{column}' not in {list(df.columns)})."
            )
        df = df[df[column] == f["value"]]

    print(df.to_string(index=False))
    return df.reset_index(drop=True)
