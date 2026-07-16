"""Feature-engineering pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import create_drug_features, print_drug_features


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=create_drug_features,
                inputs=None,
                outputs="drug_features",
                name="create_drug_features",
            ),
            # Reads `drug_features` back (FeastDataset.load -> FeastFeatureSource),
            # so Kedro runs it after the save above.
            node(
                func=print_drug_features,
                inputs="drug_features",
                outputs=None,
                name="print_drug_features",
            ),
        ]
    )
