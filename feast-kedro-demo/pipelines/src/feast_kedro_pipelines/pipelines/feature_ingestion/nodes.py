"""Nodes for the feature-ingestion pipeline."""

import pandas as pd


def create_dummy_driver_stats() -> pd.DataFrame:
    """Generate a small dummy driver-stats DataFrame.

    Columns match the ``driver_stats`` feature view schema plus the required
    ``event_timestamp``.
    """
    return pd.DataFrame(
        {
            "driver_id": [1001, 1002, 1003],
            "trips": [10, 20, 30],
            "rating": [4.5, 4.9, 3.7],
            "event_timestamp": pd.to_datetime(
                ["2024-01-01", "2024-01-01", "2024-01-01"], utc=True
            ),
        }
    )
