"""filtering pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import filter_drugs


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=filter_drugs,
                # filter_features loads from the feature service (both views);
                # filters come from runtime parameters.
                inputs=["filter_features", "params:filters"],
                outputs="filtered",  # unregistered -> in-memory result
                name="filter",
            ),
        ]
    )
