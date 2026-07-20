"""Nodes for the prime pipeline."""

import pandas as pd


def seed_candidates(candidates: pd.DataFrame) -> pd.DataFrame:
    """Copy the pristine seed into the working candidate set.

    Run once at the start of a filter request so each request starts from the
    full seed rather than a set narrowed by a previous request.
    """
    return candidates.reset_index(drop=True)
