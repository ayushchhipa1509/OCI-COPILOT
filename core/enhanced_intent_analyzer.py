# core/enhanced_intent_analyzer.py - Unified Intent Analysis & Query Classification

import json
import re
from typing import Dict, Any
from core.prompts import load_prompt
from core.llm_manager import call_llm


class EnhancedIntentAnalyzer:
    """
    Unified analyzer that does both intent analysis AND query classification.
    Replaces both intent_analyzer.py and query_classifier.py
    """

    def __init__(self):
        # Resource mappings
        self.resource_map = {
            "instances": ("instance", "compute"),
            "instance": ("instance", "compute"),
            "volumes": ("volume", "blockstorage"),
            "volume": ("volume", "blockstorage"),
            "buckets": ("bucket", "objectstorage"),
            "bucket": ("bucket", "objectstorage"),
            "vcns": ("vcn", "virtualnetwork"),
            "vcn": ("vcn", "virtualnetwork"),
            "subnets": ("subnet", "virtualnetwork"),
            "subnet": ("subnet", "virtualnetwork"),
            "security lists": ("security_list", "virtualnetwork"),
            "security list": ("security_list", "virtualnetwork"),
            "route tables": ("route_table", "virtualnetwork"),
            "load balancers": ("load_balancer", "loadbalancer"),
            "databases": ("database", "database"),
            "database": ("database", "database"),
            "users": ("user", "identity"),
            "user": ("user", "identity"),
            "groups": ("group", "identity"),
            "policies": ("policy", "identity")
        }

        # Direct fetch patterns (single API call)
        self.direct_fetch_patterns = {
            "list_users": {"service": "identity", "action": "list_users"},
            "list_groups": {"service": "identity", "action": "list_groups"},
            "list_instances": {"service": "compute", "action": "list_instances"},
            "list_volumes": {"service": "blockstorage", "action": "list_volumes"},
            "list_vcns": {"service": "virtualnetwork", "action": "list_vcns"},
            "list_security_lists": {"service": "virtualnetwork", "action": "list_security_lists"},
            "list_load_balancers": {"service": "loadbalancer", "action": "list_load_balancers"},
            "list_buckets": {"service": "objectstorage", "action": "list_buckets"}
        }

        # Multi-step indicators (require multiple API calls)
        self.multi_step_indicators = [
            "with public ip", "public ip", "public_ip",
            "without backup", "no backup", "unused",
            "attached to", "connected to", "disconnected",
            "having", "containing", "with rules",
            "ssl", "certificate", "encrypted"
        ]

    def analyze(self, query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified analysis that returns both intent AND execution strategy.
        """
        print(f"🔍 Enhanced analysis for: '{query}'")

        # Step 1: Quick pattern analysis (no LLM)
        quick_result = self._quick_analysis(query)

        if quick_result['confidence'] == 'high':
            print(
                f"✅ Quick analysis succeeded: {quick_result['execution_type']}")
            return quick_result

        # Step 2: LLM analysis for complex cases
        print(f"🤔 Quick analysis uncertain, using LLM...")
        return self._llm_analysis(query, state)

    def _quick_analysis(self, query: str) -> Dict[str, Any]:
        """
        Fast pattern-based analysis that does BOTH intent analysis AND classification.
        """
        query_lower = query.lower()

        # === INTENT ANALYSIS ===
        # Detect action
        action = None
        if re.search(r'\b(list|show|display)\b', query_lower):
            action = "list"
        elif re.search(r'\b(get|describe|details?)\b', query_lower):
            action = "get"
        elif re.search(r'\b(create|launch|start)\b', query_lower):
            action = "create"
        elif re.search(r'\b(delete|terminate|remove)\b', query_lower):
            action = "delete"
        elif re.search(r'\b(stop|shutdown)\b', query_lower):
            action = "stop"
        elif re.search(r'\b(update|modify|change)\b', query_lower):
            action = "update"

        # Detect if action is mutating (requires confirmation)
        is_mutating = action in ['create', 'delete',
                                 'stop', 'terminate', 'update', 'remove']

        # Detect resource
        primary_resource = None
        oci_service = None
        for resource_name, (resource_type, service) in self.resource_map.items():
            if resource_name in query_lower:
                primary_resource = resource_type
                oci_service = service
                break

        # Detect filtering
        requires_filtering = bool(
            re.search(r'\b(where|with|containing|filter|having)\b', query_lower))

        # Extract filter conditions
        filter_conditions = []
        if requires_filtering:
            if 'where' in query_lower:
                filter_part = query_lower.split('where', 1)[1].strip()
                filter_conditions.append(filter_part)
            if 'ingress' in query_lower and '0.0.0.0/0' in query:
                filter_conditions.append(
                    "ingress_rules contains source 0.0.0.0/0")
            if 'stopped' in query_lower or 'inactive' in query_lower:
                filter_conditions.append("lifecycle_state == STOPPED")
            if 'running' in query_lower or 'active' in query_lower:
                filter_conditions.append("lifecycle_state == RUNNING")

        # Special case: Empty bucket detection
        if (primary_resource == 'bucket' and
                any(term in query_lower for term in ['empty', 'no files', 'no objects', 'unused'])):
            requires_filtering = True
            filter_conditions.append("objects == empty")

        # === QUERY CLASSIFICATION ===
        # Check for multi-step indicators
        has_multi_step_indicators = any(
            indicator in query_lower for indicator in self.multi_step_indicators)

        # Check for direct fetch patterns
        is_direct_fetch = False
        matched_pattern = None
        for pattern, config in self.direct_fetch_patterns.items():
            if self._matches_pattern(query_lower, pattern):
                is_direct_fetch = True
                matched_pattern = pattern
                break

        # Determine execution type
        if has_multi_step_indicators:
            execution_type = "MULTI_STEP_REQUIRED"
            confidence = "high"
        elif is_direct_fetch and not has_multi_step_indicators:
            execution_type = "DIRECT_FETCH"
            confidence = "high"
        else:
            execution_type = "UNKNOWN"
            confidence = "low"

        # Determine complexity
        complexity = "simple"
        estimated_steps = 1

        if requires_filtering:
            complexity = "medium"
            estimated_steps = 2
        if len(filter_conditions) > 2 or 'and' in query_lower:
            complexity = "complex"
            estimated_steps = 3

        # Confidence level
        if not (action and primary_resource):
            confidence = "low"

        return {
            # Intent analysis results
            "primary_resource": primary_resource or "unknown",
            "action": action or "list",
            "requires_filtering": requires_filtering,
            "filter_conditions": filter_conditions,
            "complexity": complexity,
            "estimated_steps": estimated_steps,
            "oci_service": oci_service or "unknown",
            "is_mutating": is_mutating,

            # Classification results
            "execution_type": execution_type,
            "matched_pattern": matched_pattern,
            "confidence": confidence,
            "analysis_method": "pattern_matching"
        }

    def _llm_analysis(self, query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM for complex unified analysis.
        """
        try:
            # Load enhanced prompt that does both intent analysis AND classification
            prompt_template = load_prompt('enhanced_intent_analyzer')
            prompt = prompt_template.replace('{query}', query)

            messages = [
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': f'Analyze and classify: "{query}"'}
            ]

            # Use the call_llm function from state
            call_llm_func = state.get('call_llm', call_llm)
            llm_response = call_llm_func(
                state, messages, 'intent_analyzer', use_fast_model=True)

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if not json_match:
                raise ValueError("LLM response did not contain valid JSON")

            result = json.loads(json_match.group(0))
            result['confidence'] = 'high'
            result['analysis_method'] = 'llm'

            return result

        except Exception as e:
            print(f"⚠️ LLM analysis failed: {e}, using fallback")
            return {
                "primary_resource": "unknown",
                "action": "list",
                "requires_filtering": False,
                "filter_conditions": [],
                "complexity": "simple",
                "estimated_steps": 1,
                "oci_service": "compute",
                "is_mutating": False,
                "execution_type": "MULTI_STEP_REQUIRED",  # Default to safe option
                "confidence": "low",
                "analysis_method": "fallback"
            }

    def _matches_pattern(self, query_lower: str, pattern: str) -> bool:
        """Check if query matches a direct fetch pattern."""
        pattern_parts = pattern.split('_')

        # Check for action
        action_match = any(action in query_lower for action in [
                           'list', 'show', 'display', 'get all'])

        # Check for resource
        resource_match = pattern_parts[1] in query_lower or pattern_parts[1].replace(
            '_', ' ') in query_lower

        return action_match and resource_match

    def get_execution_strategy(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed execution strategy based on analysis."""
        execution_type = analysis_result.get('execution_type')

        if execution_type == "DIRECT_FETCH":
            return {
                "strategy": "template_based",
                "use_llm": False,
                "estimated_time": "fast",
                "api_calls": 1,
                "description": "Single API call with optional filtering"
            }
        elif execution_type == "MULTI_STEP_REQUIRED":
            return {
                "strategy": "llm_planned",
                "use_llm": True,
                "estimated_time": "medium",
                "api_calls": "multiple",
                "description": "Multiple API calls with intelligent filtering"
            }
        else:
            return {
                "strategy": "llm_planned",
                "use_llm": True,
                "estimated_time": "medium",
                "api_calls": "unknown",
                "description": "LLM-based planning for complex query"
            }


def analyze_intent_and_classify(query: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function that does both intent analysis AND query classification.
    """
    analyzer = EnhancedIntentAnalyzer()
    return analyzer.analyze(query, state)
