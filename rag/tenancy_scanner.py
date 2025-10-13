# rag/tenancy_scanner.py
# Master Tenancy Scanner – per-resource indexing with pagination and rich metadata
import oci
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import json

from core.state import AgentState
from oci_ops.clients import get_client
from oci_ops.pagination import get_all_items
from rag.embeddings import get_embedding
from rag.vectorstore import add_to_store

SCAN_TS = lambda: datetime.now(timezone.utc).isoformat()

# (CANONICAL_TYPE and other constants remain the same)
CANONICAL_TYPE: Dict[Tuple[str, str], str] = {
    ("identity", "list_users"): "user",
    ("identity", "list_groups"): "group",
    ("identity", "list_policies"): "policy",
    ("compute", "list_instances"): "instance",
    ("compute", "list_images"): "image",
    ("blockstorage", "list_volumes"): "volume",
    ("blockstorage", "list_boot_volumes"): "boot_volume",
    ("virtualnetwork", "list_vcns"): "vcn",
    ("virtualnetwork", "list_subnets"): "subnet",
    ("virtualnetwork", "list_security_lists"): "security_list",
    ("virtualnetwork", "list_route_tables"): "route_table",
    ("virtualnetwork", "list_network_security_groups"): "nsg",
    ("objectstorage", "list_buckets"): "bucket",
    ("database", "list_db_systems"): "db_system",
    ("database", "list_autonomous_databases"): "autonomous_database",
    ("monitoring", "list_alarms"): "alarm",
    ("loadbalancer", "list_load_balancers"): "load_balancer",
}

COMMON_FIELDS = [
    "id", "ocid", "display_name", "name", "email", "description",
    "lifecycle_state", "shape", "size_in_gbs", "compartment_id",
    "availability_domain", "region", "namespace", "time_created",
    "defined_tags", "freeform_tags", "db_workload", "is_auto_tune_enabled",
    "public_access_type", "image_id", "metadata", "cidr_block", "statements"
]

AD_REQUIRED = {("blockstorage", "list_boot_volumes")}
SUBTREE_REQUIRED = {("optimizer", "list_recommendations"), ("cloudguard", "list_problems")}
TENANCY_LEVEL_ONLY = {("identity", "list_users"), ("identity", "list_groups"), ("identity", "list_policies")}

def _safe_attr(obj: Any, attr: str, default=None):
    return getattr(obj, attr, default)

def _obj_to_dict(obj: Any) -> Dict[str, Any]:
    d = {f: val for f in COMMON_FIELDS if (val := _safe_attr(obj, f)) is not None}
    if "id" in d and "ocid" not in d:
        d["ocid"] = d["id"]
    return d

def _resource_text(resource_type: str, data: Dict[str, Any], findings: List[str]) -> str:
    parts = [f"type: {resource_type}"]
    for k, v in data.items():
        if v is not None and not isinstance(v, (dict, list)):
            parts.append(f"{k}: {v}")
    if findings:
        parts.append("Findings: " + " | ".join(findings))
    return " ".join(parts)

def _canonical_type(service: str, operation: str) -> str:
    return CANONICAL_TYPE.get((service, operation), f"{service}_{operation}")

def _list_availability_domains(identity_client, tenancy_id: str) -> List[str]:
    try:
        return [ad.name for ad in identity_client.list_availability_domains(tenancy_id).data]
    except Exception as e:
        print(f"Error listing availability domains: {e}")
        return []

def _scan_object_storage(state: AgentState, compartments: List[Dict[str, Any]], namespace: str) -> List[Dict[str, Any]]:
    results = []
    creds = state.get("oci_creds")
    os_client = get_client("objectstorage", creds)

    for comp in compartments:
        items = get_all_items(os_client.list_buckets, namespace_name=namespace, compartment_id=comp["id"])
        for obj in items:
            if hasattr(obj, 'to_dict'):
                d = obj.to_dict()
            else:
                d = _obj_to_dict(obj)
            findings = []
            if d.get("public_access_type") != "NoPublicAccess":
                findings.append("Bucket has public access.")
            
            # Count objects as a finding
            try:
                # The list_objects call returns a ListObjects object, the actual objects are in the 'objects' attribute.
                object_summary_list = get_all_items(os_client.list_objects, namespace_name=namespace, bucket_name=d["name"])
                object_count = len(object_summary_list.objects)
                if object_count > 0:
                    findings.append(f"Contains {object_count} objects.")
            except Exception as e:
                print(f"Could not list objects for bucket {d.get('name')}: {e}")

            meta = {"resource_type": "bucket", "service": "objectstorage", "ocid": d.get("ocid"), "name": d.get("name")}
            text = _resource_text("bucket", d, findings)
            emb = get_embedding(text)
            add_to_store(text, {k: v for k, v in meta.items() if v is not None}, emb)
            results.append({"text": text, "meta": meta})
    return results

def _scan_generic_service(state: AgentState, service: str, operation: str, comp_id: str, ad: Optional[str] = None) -> List[Dict[str, Any]]:
    results = []
    creds = state.get("oci_creds")
    client = get_client(service, creds)
    if not client:
        return []

    params = {"compartment_id": comp_id}
    if (service, operation) in AD_REQUIRED and ad:
        params["availability_domain"] = ad
    if (service, operation) in SUBTREE_REQUIRED:
        params["compartment_id_in_subtree"] = True

    items = get_all_items(getattr(client, operation), **params)
    rtype = _canonical_type(service, operation)

    # Get helper clients for deep scanning
    compute_client = get_client("compute", creds)
    vn_client = get_client("virtualnetwork", creds)

    for obj in items:
        if hasattr(obj, 'to_dict'):
            d = obj.to_dict()
        else:
            d = _obj_to_dict(obj)
        findings = []

        # Handle policy statements
        if rtype == "policy":
            statements = d.get("statements")
            if statements and isinstance(statements, list):
                findings.extend(statements)

        # --- DEEP SCAN LOGIC --- 
        try:
            if rtype == "instance":
                if not d.get("metadata", {}).get("ssh_authorized_keys"):
                    findings.append("Instance does not have SSH key-based authentication.")
                vnics = get_all_items(compute_client.list_vnic_attachments, compartment_id=comp_id, instance_id=d.get("id"))
                for vnic_attachment in vnics:
                    vnic = vn_client.get_vnic(vnic_attachment.vnic_id).data.to_dict()
                    for nsg_id in vnic.get("nsg_ids", []):
                        rules = get_all_items(vn_client.list_network_security_group_security_rules, network_security_group_id=nsg_id)
                        if any(rule.direction == "INGRESS" and rule.source == "0.0.0.0/0" for rule in rules):
                            findings.append("NSG allows unrestricted ingress.")
                            break # Found one, no need to check others for this instance
            elif rtype == "volume":
                attachments = get_all_items(compute_client.list_volume_attachments, compartment_id=comp_id, volume_id=d.get("id"))
                if not attachments:
                    findings.append("Volume is unattached.")
            elif rtype == "vcn":
                if d.get("cidr_block") == "0.0.0.0/0":
                    findings.append("VCN has an open CIDR block.")
            elif rtype == "autonomous_database":
                if d.get("db_workload") != "OLTP":
                    findings.append(f"ADB is not optimized for OLTP workloads, it is {d.get('db_workload')}.")
        except Exception as e:
            print(f"Deep scan error for {d.get('id')}: {e}")
        # --- END DEEP SCAN --- 

        meta = {"resource_type": rtype, "service": service, "ocid": d.get("ocid"), "name": d.get("display_name") or d.get("name")}
        if rtype == "user":
            meta["email"] = d.get("email")
            
        text = _resource_text(rtype, d, findings)
        emb = get_embedding(text)
        add_to_store(text, {k: v for k, v in meta.items() if v is not None}, emb)
        results.append({"text": text, "meta": meta})
    return results


def _list_all_compartments(state: AgentState) -> List[Dict[str, Any]]:
    creds = state.get("oci_creds")
    tenancy_id = creds.get("tenancy")
    if not tenancy_id:
        return []
    try:
        identity_client = get_client("identity", creds)
        all_compartments = get_all_items(
            identity_client.list_compartments,
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ANY"
        )
        # Filter for active compartments and include the root
        active_compartments = [{"id": c.id, "name": c.name} for c in all_compartments if c.lifecycle_state == "ACTIVE"]
        return active_compartments + [{"id": tenancy_id, "name": "Tenancy Root"}]
    except Exception as e:
        print(f"Error listing compartments: {e}")
        return [{"id": tenancy_id, "name": "Tenancy Root"}] if tenancy_id else []


def master_tenancy_scan(state: AgentState) -> Dict[str, Any]:
    """
    Full tenancy deep scan.
    """
    print("🔍 Master Tenancy Deep Scan - START")
    creds = state.get("oci_creds", {})
    tenancy_id = creds.get("tenancy")
    if not tenancy_id:
        print("❌ Tenancy OCID not found in state.")
        return {}

    compartments = _list_all_compartments(state)
    identity_client = get_client("identity", creds)
    os_client = get_client("objectstorage", creds)
    try:
        namespace = os_client.get_namespace().data
    except Exception as e:
        print(f"Failed to get Object Storage namespace: {e}")
        namespace = None
        
    ads = _list_availability_domains(identity_client, tenancy_id)
    
    # Scan Plan for services that run on a per-compartment basis
    compartment_services_plan = [
        ("compute", "list_instances"), 
        ("compute", "list_images"),
        ("blockstorage", "list_volumes"),
        ("blockstorage", "list_boot_volumes"), 
        ("virtualnetwork", "list_vcns"),
        ("virtualnetwork", "list_subnets"), 
        ("virtualnetwork", "list_security_lists"),
        ("virtualnetwork", "list_route_tables"), 
        ("virtualnetwork", "list_network_security_groups"),
        ("database", "list_db_systems"), 
        ("database", "list_autonomous_databases"),
        ("monitoring", "list_alarms"), 
        ("loadbalancer", "list_load_balancers"),
    ]

    all_docs = []

    for comp in compartments:
        print(f"📦 Scanning compartment: {comp.get('name')}, ({comp.get('id')})")
        if namespace:
            all_docs.extend(_scan_object_storage(state, [comp], namespace))
        for service, op in compartment_services_plan:
            try:
                if (service, op) in AD_REQUIRED and ads:
                    for ad in ads:
                        all_docs.extend(_scan_generic_service(state, service, op, comp["id"], ad=ad))
                else:
                    all_docs.extend(_scan_generic_service(state, service, op, comp["id"]))
            except Exception as e:
                print(f"{service}.{op} scan failed for {comp['id']}: {e}")

    # Scan tenancy-level services
    print("📦 Scanning tenancy-level services...")
    tenancy_level_plan = SUBTREE_REQUIRED.union(TENANCY_LEVEL_ONLY)
    for service, op in tenancy_level_plan:
        try:
            all_docs.extend(_scan_generic_service(state, service, op, tenancy_id))
        except Exception as e:
            print(f"{service}.{op} scan failed for tenancy: {e}")

    print(f"✅ Master Tenancy Deep Scan - DONE, indexed resources: {len(all_docs)}")
    return {
        "indexed_resources": len(all_docs),
        "compartments_scanned": len(compartments),
        "timestamp": SCAN_TS(),
    }