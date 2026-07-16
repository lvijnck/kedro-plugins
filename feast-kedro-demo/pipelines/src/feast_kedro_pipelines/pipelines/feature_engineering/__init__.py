"""Feature-engineering pipeline: compute drug features and write to Feast."""

from .pipeline import create_pipeline

__all__ = ["create_pipeline"]
