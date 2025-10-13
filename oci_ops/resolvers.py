# oci_ops/resolvers.py
from typing import Dict, Any, List
from .clients import get_client
from .pagination import get_all_items


def get_all_active_compartments(config: Dict[str, Any]) -> List[str]:
    """Returns the tenancy OCID plus all active child compartment OCIDs."""
    tenancy_id = config.get("tenancy")
    if not tenancy_id:
        return []
    try:
        identity_client = get_client("identity", config)
        all_compartments = get_all_items(
            identity_client.list_compartments,
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ANY"
        )
        active_cids = [
            c.id for c in all_compartments if c.lifecycle_state == "ACTIVE"]
        # Ensure tenancy is first and there are no duplicates
        return list(dict.fromkeys([tenancy_id] + active_cids))
    except Exception:
        return [tenancy_id]  # Fallback to just the tenancy
