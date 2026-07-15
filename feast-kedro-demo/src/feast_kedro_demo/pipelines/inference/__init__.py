"""Inference pipeline: read features from Feast and predict a trip price."""

from .pipeline import create_pipeline

__all__ = ["create_pipeline"]
