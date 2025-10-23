#!/usr/bin/env python3
"""
Debug parameter parsing step by step
"""


def debug_parsing():
    user_input = "compartment_id: ocid1.compartment.oc1..aaaaaaaaf7eluqwc4n2twn3urhqniqycqpo5sn3ytxescicvbg2tccxcntia display_name: my-test-vcn cidr_block: 10.0.0.0/16"
    missing_params = ["compartment_id", "display_name", "cidr_block"]

    print(f"Input: {user_input}")
    print(f"Missing: {missing_params}")

    # Test the space-based parsing logic
    parts = user_input.split()
    print(f"Split parts: {parts}")

    selected_params = {}
    i = 0
    while i < len(parts):
        part = parts[i]
        print(f"Processing part {i}: '{part}'")

        if ':' in part and i + 1 < len(parts):
            key = part.rstrip(':')
            print(f"  Found key: '{key}'")

            if key in missing_params:
                print(f"  Key '{key}' is in missing_params")
                # Collect the value (might be multiple words)
                value_parts = []
                j = i + 1
                print(f"  Starting to collect value from position {j}")

                while j < len(parts) and not (':' in parts[j] and parts[j].rstrip(':') in missing_params):
                    print(f"    Adding '{parts[j]}' to value")
                    value_parts.append(parts[j])
                    j += 1

                value = ' '.join(value_parts)
                selected_params[key] = value
                print(f"  Final value for '{key}': '{value}'")
                i = j
            else:
                print(f"  Key '{key}' not in missing_params")
                i += 1
        else:
            print(f"  No colon or no next part")
            i += 1

    print(f"Final result: {selected_params}")


if __name__ == "__main__":
    debug_parsing()


