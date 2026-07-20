"""feature_b pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import create_feature_b


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=create_feature_b,
                inputs="input",  # current candidate pairs (catalog)
                outputs="feature_b",  # -> feature_b_view (see catalog.yml)
                name="create_feature_b",
            ),
        ]
    )
