"""Inference pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import predict_trip_price


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=predict_trip_price,
                inputs=["driver_stats_features", "params:inference_params.driver_id", "params:inference_params.distance"],
                outputs="predicted_trip_prices",
                name="predict_trip_price",
            ),
        ]
    )
