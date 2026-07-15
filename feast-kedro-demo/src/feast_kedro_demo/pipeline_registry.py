"""Project pipelines."""

from kedro.pipeline import Pipeline

from feast_kedro_demo.pipelines import feature_ingestion, inference


def register_pipelines() -> dict[str, Pipeline]:
    ingestion = feature_ingestion.create_pipeline()
    infer = inference.create_pipeline()
    return {
        # Full demo: ingest features, then run inference off them.
        "__default__": ingestion + infer,
        "feature_ingestion": ingestion,
        "inference": infer,
    }
