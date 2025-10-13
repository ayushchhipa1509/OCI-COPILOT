# oci_ops/transformers.py
from typing import Any, Dict


def _safe_get(obj: Any, attr: str, default=None):
    """Safely gets an attribute from an object."""
    return getattr(obj, attr, default)


def instance_row(instance_obj: Any) -> Dict[str, Any]:
    """Transforms an OCI Instance object into a simple dictionary."""
    return {
        "id": _safe_get(instance_obj, "id"),
        "display_name": _safe_get(instance_obj, "display_name"),
        "lifecycle_state": _safe_get(instance_obj, "lifecycle_state"),
        "shape": _safe_get(instance_obj, "shape"),
        "compartment_id": _safe_get(instance_obj, "compartment_id"),
    }


def bucket_row(bucket_obj: Any) -> Dict[str, Any]:
    """Transforms an OCI Bucket object into a simple dictionary."""
    return {
        "name": _safe_get(bucket_obj, "name"),
        "namespace": _safe_get(bucket_obj, "namespace"),
        "compartment_id": _safe_get(bucket_obj, "compartment_id"),
        "time_created": str(_safe_get(bucket_obj, "time_created")),
    }
