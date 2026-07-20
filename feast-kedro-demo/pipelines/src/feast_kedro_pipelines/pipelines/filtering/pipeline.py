"""filtering pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import filter_drugs


def create_pipeline(
    input_dataset: str = "candidates",
    output_dataset: str = "survivors",
    filters: list[dict] | None = None,
    step: int = 0,
    **kwargs,
) -> Pipeline:
    """Build a filtering pipeline reading candidates from ``input_dataset``.

    ``filters`` are bound into the node at build time (each entry
    ``{"feature": ..., "value": ...}``); an empty/absent list keeps every pair.
    ``step`` disambiguates node names when several filters are chained together.
    """
    bound = filters or []

    def apply(filter_features, candidates, _filters=bound):
        return filter_drugs(filter_features, candidates, _filters)

    apply.__name__ = f"filter_drugs_{step}"

    return pipeline(
        [
            node(
                func=apply,
                inputs=["filter_features", input_dataset],
                outputs=output_dataset,
                name=f"filter_{step}",
            ),
        ]
    )
