"""feature_b pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import create_feature_b


# NOTE: Set defaults here so pipeline works undeer normal circumstances, 
# dynamic filtering pipeline will override these. 
def create_pipeline(
    input_dataset: str = "candidates",
    featured: str = "feature_b_pairs",
    step: int = 0,
    **kwargs,
) -> Pipeline:
    """Build the feature_b pipeline reading candidates from ``input_dataset``.

    ``featured`` is the passthrough of processed pairs (used to order a filter
    step after this one); ``step`` disambiguates node names when several feature
    pipelines are chained together.
    """
    return pipeline(
        [
            node(
                func=create_feature_b,
                inputs=input_dataset,
                outputs=["feature_b", featured],  # feature_b -> feature_b_view
                name=f"create_feature_b_{step}",
            ),
        ]
    )
