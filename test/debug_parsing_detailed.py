#!/usr/bin/env python3
"""
Debug parameter parsing step by step with the actual function
"""

from nodes.presentation_node import _parse_parameter_response
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def debug_parsing_detailed():
    user_input = "compartment_id: ocid1.compartment.oc1..aaaaaaaaf7eluqwc4n2twn3urhqniqycqpo5sn3ytxescicvbg2twn3urhqniqycqpo5sn3ytxescicvbg2tccxcntia display_name: my-test-vcn cidr_block: 10.0.0.0/16"
    missing_params = ["compartment_id", "display_name", "cidr_block"]

    print(f"Input: {user_input}")
    print(f"Missing: {missing_params}")

    # Test the actual function
    success, parsed_params = _parse_parameter_response(
        user_input, missing_params, None, None)
    print(f"Success: {success}")
    print(f"Parsed Parameters: {parsed_params}")

    # Check if all parameters were parsed correctly
    for param in missing_params:
        if param in parsed_params:
            print(f"✅ {param}: {parsed_params[param]}")
        else:
            print(f"❌ {param}: MISSING")


if __name__ == "__main__":
    debug_parsing_detailed()


