"""Entity join keys, shared by the pipelines and the service.

These mirror the Feast entity ``join_keys`` (``drug`` / ``disease``) defined in
the feature repo, and are the columns that identify a candidate pair.
"""

KEY_COLUMNS = ["drug_kg_node_id", "disease_kg_node_id"]
