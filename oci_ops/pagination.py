# oci_ops/pagination.py
from typing import Any, List, Callable
import oci

def get_all_items(call: Callable[..., Any], **kwargs) -> List[Any]:
    """
    Calls an OCI SDK list_* method and handles pagination to return all items.
    """
    try:
        return oci.pagination.list_call_get_all_results(call, **kwargs).data
    except oci.exceptions.ServiceError as e:
        # Let 404s (Not Found) pass silently, as they are expected for some compartments.
        # Log other service errors.
        if e.status != 404:
            print(f"Service error in get_all_items for {call.__name__}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in get_all_items for {call.__name__}: {e}")
        return []