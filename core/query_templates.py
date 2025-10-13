# core/query_templates.py - Template-based planning for common queries

from typing import Dict, Any, Optional


class QueryTemplates:
    """Pre-defined templates for common OCI query patterns."""

    def __init__(self):
        # OCI API method mappings for DIRECT_FETCH queries
        self.api_methods = {
            # Compute Service
            "instance": "list_instances",
            "image": "list_images",
            "shape": "list_shapes",

            # Storage Service
            "volume": "list_volumes",
            "boot_volume": "list_boot_volumes",
            "bucket": "list_buckets",

            # Networking Service
            "vcn": "list_vcns",
            "subnet": "list_subnets",
            "security_list": "list_security_lists",
            "route_table": "list_route_tables",
            "network_security_group": "list_network_security_groups",

            # Load Balancer Service
            "load_balancer": "list_load_balancers",
            "backend_set": "list_backend_sets",

            # Database Service
            "database": "list_db_systems",
            "autonomous_database": "list_autonomous_databases",

            # Identity Service
            "user": "list_users",
            "group": "list_groups",
            "policy": "list_policies",
            "compartment": "list_compartments",

            # Monitoring Service
            "alarm": "list_alarms",
            "metric": "list_metrics",

            # Cloud Guard Service
            "detector": "list_detectors",
            "problem": "list_problems",

            # Optimizer Service
            "recommendation": "list_recommendations"
        }

        # Direct fetch patterns with built-in filtering
        self.direct_fetch_patterns = {
            # State-based filtering (single API call with parameters)
            "running_instances": {
                "api_method": "list_instances",
                "service": "compute",
                "filters": [{"field": "lifecycle_state", "value": "RUNNING"}],
                "built_in_filter": True
            },
            "stopped_instances": {
                "api_method": "list_instances",
                "service": "compute",
                "filters": [{"field": "lifecycle_state", "value": "STOPPED"}],
                "built_in_filter": True
            },
            "active_users": {
                "api_method": "list_users",
                "service": "identity",
                "filters": [{"field": "lifecycle_state", "value": "ACTIVE"}],
                "built_in_filter": True
            },
            "available_volumes": {
                "api_method": "list_volumes",
                "service": "blockstorage",
                "filters": [{"field": "lifecycle_state", "value": "AVAILABLE"}],
                "built_in_filter": True
            }
        }

    def get_template_plan(self, intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate a plan from templates if possible.
        Returns None if no template matches.
        """
        resource = intent.get('primary_resource')
        action = intent.get('action')
        requires_filtering = intent.get('requires_filtering', False)
        filter_conditions = intent.get('filter_conditions', [])

        # Only handle list actions with templates
        if action != 'list':
            return None

        # First, check for direct fetch patterns
        direct_pattern = self._check_direct_fetch_patterns(intent)
        if direct_pattern:
            print(
                f"📋 Using direct fetch pattern: {direct_pattern['pattern_name']}")
            return direct_pattern

        # Get API method for standard templates
        api_method = self.api_methods.get(resource)
        if not api_method:
            return None

        print(
            f"📋 Using standard template for: {resource} (method: {api_method})")

        if requires_filtering:
            return self._create_filtering_plan(resource, api_method, filter_conditions)
        else:
            return self._create_simple_list_plan(resource, api_method)

    def _check_direct_fetch_patterns(self, intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if query matches any direct fetch patterns.
        """
        resource = intent.get('primary_resource')
        filter_conditions = intent.get('filter_conditions', [])

        # Check for running instances pattern
        if (resource == 'instance' and
            any('running' in condition.lower() or 'active' in condition.lower()
                for condition in filter_conditions)):
            return {
                "type": "direct_fetch",
                "pattern_name": "running_instances",
                "api_method": "list_instances",
                "service": "compute",
                "filters": [{"field": "lifecycle_state", "value": "RUNNING"}],
                "built_in_filter": True,
                "template_used": True
            }

        # Check for stopped instances pattern
        if (resource == 'instance' and
            any('stopped' in condition.lower() or 'inactive' in condition.lower()
                for condition in filter_conditions)):
            return {
                "type": "direct_fetch",
                "pattern_name": "stopped_instances",
                "api_method": "list_instances",
                "service": "compute",
                "filters": [{"field": "lifecycle_state", "value": "STOPPED"}],
                "built_in_filter": True,
                "template_used": True
            }

        # Check for active users pattern
        if (resource == 'user' and
                any('active' in condition.lower() for condition in filter_conditions)):
            return {
                "type": "direct_fetch",
                "pattern_name": "active_users",
                "api_method": "list_users",
                "service": "identity",
                "filters": [{"field": "lifecycle_state", "value": "ACTIVE"}],
                "built_in_filter": True,
                "template_used": True
            }

        # Check for available volumes pattern
        if (resource == 'volume' and
                any('available' in condition.lower() for condition in filter_conditions)):
            return {
                "type": "direct_fetch",
                "pattern_name": "available_volumes",
                "api_method": "list_volumes",
                "service": "blockstorage",
                "filters": [{"field": "lifecycle_state", "value": "AVAILABLE"}],
                "built_in_filter": True,
                "template_used": True
            }

        # Check for empty buckets pattern
        if (resource == 'bucket' and
                any(term in condition.lower() for condition in filter_conditions
                    for term in ['empty', 'no files', 'no objects', 'unused', 'vacant', 'bare', 'clean'])):
            return {
                "type": "list_with_filter",
                "pattern_name": "empty_buckets",
                "api_method": "list_buckets",
                "service": "objectstorage",
                "requires_filtering": True,
                "filters": [{"field": "objects", "value": "empty", "type": "object_count_check"}],
                "built_in_filter": False,  # Requires custom filtering logic
                "template_used": True
            }

        return None

    def _create_simple_list_plan(self, resource: str, api_method: str) -> Dict[str, Any]:
        """Create a simple list plan (no filtering)."""
        return {
            "type": "simple_list",
            "resource": resource,
            "api_method": api_method,
            "requires_filtering": False,
            "all_compartments": True,
            "template_used": True
        }

    def _create_filtering_plan(self, resource: str, api_method: str,
                               filter_conditions: list) -> Dict[str, Any]:
        """Create a filtering plan (list + filter in code)."""

        # Parse filter conditions
        filters = []
        for condition in filter_conditions:
            filter_info = self._parse_filter_condition(condition)
            if filter_info:
                filters.append(filter_info)

        return {
            "type": "list_with_filter",
            "resource": resource,
            "api_method": api_method,
            "requires_filtering": True,
            "filters": filters,
            "all_compartments": True,
            "template_used": True
        }

    def _parse_filter_condition(self, condition: str) -> Optional[Dict[str, Any]]:
        """Parse a filter condition into structured format."""
        condition_lower = condition.lower()

        # Parse different filter types
        filter_info = {}

        # Lifecycle state filters
        if 'stopped' in condition_lower or 'inactive' in condition_lower:
            filter_info['field'] = 'lifecycle_state'
            filter_info['operator'] = '=='
            filter_info['value'] = 'STOPPED'
            filter_info['type'] = 'simple_equality'

        elif 'running' in condition_lower or 'active' in condition_lower:
            filter_info['field'] = 'lifecycle_state'
            filter_info['operator'] = '=='
            filter_info['value'] = 'RUNNING'
            filter_info['type'] = 'simple_equality'

        elif 'available' in condition_lower:
            filter_info['field'] = 'lifecycle_state'
            filter_info['operator'] = '=='
            filter_info['value'] = 'AVAILABLE'
            filter_info['type'] = 'simple_equality'

        # Ingress rules filter
        elif 'ingress' in condition_lower and '0.0.0.0/0' in condition:
            filter_info['field'] = 'ingress_security_rules'
            filter_info['operator'] = 'contains'
            filter_info['value'] = '0.0.0.0/0'
            filter_info['type'] = 'nested_check'
            filter_info['nested_field'] = 'source'

        # Shape filter
        elif 'shape' in condition_lower:
            filter_info['field'] = 'shape'
            filter_info['operator'] = 'contains'
            filter_info['value'] = condition.split(
                'shape')[1].strip().strip('"\'')
            filter_info['type'] = 'simple_contains'

        # Compartment name filter
        elif 'compartment' in condition_lower:
            filter_info['field'] = 'compartment_name'
            filter_info['operator'] = '=='
            filter_info['value'] = condition.split(
                'compartment')[1].strip().strip('"\'')
            filter_info['type'] = 'compartment_filter'

        return filter_info if filter_info else None


def get_template_plan(intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get a template plan.
    """
    templates = QueryTemplates()
    return templates.get_template_plan(intent)
