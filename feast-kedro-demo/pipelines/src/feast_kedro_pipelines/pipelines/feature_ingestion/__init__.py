"""Feature-ingestion pipeline: generate dummy driver stats and write to Feast."""

from .pipeline import create_pipeline

__all__ = ["create_pipeline"]
