"""Inference pipeline definition.

Currently codified in Kedro and exposed over HTTP via Kedro's built-in server. Alternatively one could
setup a FastAPI API and expose an inference endpoint that leverages the feast client directly to get the features and score the drug-disease pair.
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import predict_repurposing_score


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=predict_repurposing_score,
                # drug_features loads as a FeastFeatureSource; the drug/disease
                # ids come from runtime parameters.
                inputs=[
                    "drug_features",
                    "params:drug_kg_node_id",
                    "params:disease_kg_node_id",
                ],
                outputs="repurposing_scores",
                name="predict_repurposing_score",
            ),
        ]
    )
