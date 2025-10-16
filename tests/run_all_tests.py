#!/usr/bin/env python3
"""
Run all deployment workflow tests
"""

import sys
import os
sys.path.append('.')


def run_all_tests():
    """Run all deployment workflow tests"""

    print('🚀 RUNNING ALL DEPLOYMENT WORKFLOW TESTS')
    print('=' * 60)
    print()

    # Test files to run
    test_files = [
        'test_bucket_creation.py',
        'test_volume_creation.py',
        'test_vcn_creation.py',
        'test_instance_creation.py',
        'test_loadbalancer_creation.py',
        'test_comprehensive_flows.py',
        'test_parameter_gathering.py',
        'test_confirmation_flows.py',
        'test_error_handling.py',
        'test_routing_flows.py'
    ]

    results = {}

    for test_file in test_files:
        print(f'🧪 Running {test_file}...')
        print('-' * 40)

        try:
            # Import and run the test
            module_name = test_file.replace('.py', '')
            module = __import__(f'tests.{module_name}', fromlist=[module_name])

            # Get the test function name - handle different naming patterns
            if module_name in ['test_comprehensive_flows', 'test_parameter_gathering', 'test_confirmation_flows', 'test_error_handling', 'test_routing_flows']:
                test_func_name = f'run_{module_name.replace("test_", "")}_tests'
            else:
                test_func_name = f'test_{module_name.replace("test_", "")}_workflow'

            # Handle specific function name variations
            if module_name == 'test_comprehensive_flows':
                test_func_name = 'run_comprehensive_tests'
            elif module_name == 'test_confirmation_flows':
                test_func_name = 'run_confirmation_tests'
            elif module_name == 'test_routing_flows':
                test_func_name = 'run_routing_tests'
            test_func = getattr(module, test_func_name)

            # Run the test
            test_func()
            results[test_file] = 'PASS'

        except Exception as e:
            print(f'❌ {test_file} FAILED: {e}')
            results[test_file] = 'FAIL'

        print()
        print('=' * 60)
        print()

    # Summary
    print('📊 FINAL SUMMARY:')
    print('=' * 60)

    passed = 0
    failed = 0

    for test_file, result in results.items():
        status_emoji = '✅' if result == 'PASS' else '❌'
        print(f'{status_emoji} {test_file}: {result}')

        if result == 'PASS':
            passed += 1
        else:
            failed += 1

    print()
    print(f'📈 RESULTS: {passed} PASSED, {failed} FAILED')

    if failed == 0:
        print('🎉 ALL TESTS PASSED!')
    else:
        print(f'⚠️ {failed} TESTS FAILED - Check the output above for details')


if __name__ == "__main__":
    run_all_tests()
