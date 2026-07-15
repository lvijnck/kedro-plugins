"""Feature-ingestion pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import create_dummy_driver_stats


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=create_dummy_driver_stats,
                inputs=None,
                outputs="driver_stats_features",
                name="create_driver_stats_features",
            ),
        ]
    )
