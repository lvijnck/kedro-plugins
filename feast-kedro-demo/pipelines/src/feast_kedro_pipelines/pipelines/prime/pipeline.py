"""prime pipeline definition."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import seed_candidates


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=seed_candidates,
                inputs="candidates",  # pristine seed CSV
                outputs="input",  # working set CSV
                name="seed_candidates",
            ),
        ]
    )
