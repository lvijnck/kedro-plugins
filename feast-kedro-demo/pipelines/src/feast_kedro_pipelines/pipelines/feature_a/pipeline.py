"""feature_a pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import create_feature_a


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=create_feature_a,
                inputs="input",  # current candidate pairs (catalog)
                outputs="feature_a",  # -> feature_a_view (see catalog.yml)
                name="create_feature_a",
            ),
        ]
    )
