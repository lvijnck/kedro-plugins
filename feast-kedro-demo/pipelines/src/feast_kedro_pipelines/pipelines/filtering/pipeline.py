"""filtering pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import filter_drugs


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=filter_drugs,
                # filter_features loads from the feature service (both views);
                # candidates is the current working set; filters are runtime params.
                inputs=["filter_features", "input", "params:filters"],
                outputs="iterative_output",  # survivors -> working-set file
                name="filter",
            ),
        ]
    )
