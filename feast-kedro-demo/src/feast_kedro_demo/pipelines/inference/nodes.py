"""Nodes for the inference pipeline."""

import pandas as pd

from kedro_datasets_experimental.feast.feast_dataset import FeastFeatureSource

# Simple fare model: base fare + per-km rate, nudged by the driver's rating.
BASE_FARE = 2.5
PER_KM = 1.2


def predict_trip_price(
    driver_features: FeastFeatureSource,
    driver_id: int,
    distance: float,
) -> pd.DataFrame:
    """Predict the expected trip price for ``driver_id`` over ``distance`` km.

    Reads the driver's latest features from Feast's offline store via a
    point-in-time join, then applies a toy fare model.
    """
    entity_df = pd.DataFrame(
        {
            "driver_id": [driver_id],
            "event_timestamp": [pd.Timestamp.now(tz="UTC")],
        }
    )
    features = driver_features.get_historical_features(entity_df)

    rating = features["rating"].iloc[0]
    rating = 5.0 if pd.isna(rating) else float(rating)

    predicted_price = BASE_FARE + PER_KM * float(distance) * (rating / 5.0)

    return pd.DataFrame(
        {
            "driver_id": [driver_id],
            "distance": [float(distance)],
            "predicted_trip_price": [round(predicted_price, 2)],
            "event_timestamp": [pd.Timestamp.now(tz="UTC")],
        }
    )
