"""Project pipelines."""

from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline


def register_pipelines() -> dict[str, Pipeline]:
    pipelines = find_pipelines()
    # `filtering` is excluded from the default run: it reads the feature service
    # and is only meaningful when driven (with bound filters) by the /filter
    # endpoint. Start from an empty Pipeline so a scoped run never sums to int 0.
    pipelines["__default__"] = sum(
        (v for k, v in pipelines.items() if k != "filtering"), Pipeline([])
    )
    return pipelines
