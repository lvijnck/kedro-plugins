"""Inference pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import predict_trip_price


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=predict_trip_price,
                # driver_stats_features loads as a FeastFeatureSource; the
                # driver id and distance come from runtime parameters.
                inputs=["driver_stats_features", "params:driver_id", "params:distance"],
                outputs="predicted_trip_prices",
                name="predict_trip_price",
            ),
        ]
    )
