#!/usr/bin/env python3
"""
Main test runner for ComputerQuest tests

This script provides options to:
1. Run all tests
2. Run a specific test module
3. Generate coverage reports
"""

import argparse
import os
import sys
import unittest

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_all_tests(with_coverage=False):
    """Run all unit tests"""
    if PYTEST_AVAILABLE and with_coverage:
        print("=" * 70)
        print("Running KodeKloud Computer Quest Tests with Coverage")
        print("=" * 70)

        pytest_args = [
            '--cov=computerquest',
            '--cov-report=term',
            '--cov-report=html',
            os.path.dirname(__file__)
        ]
        return pytest.main(pytest_args)
    else:
        # Find all test files
        loader = unittest.TestLoader()
        test_suite = loader.discover(os.path.dirname(__file__), pattern="test_*.py")

        # Create test runner
        runner = unittest.TextTestRunner(verbosity=2)

        # Run tests
        print("=" * 70)
        print("Running KodeKloud Computer Quest Unit Tests")
        print("=" * 70)

        result = runner.run(test_suite)

        print("\n" + "=" * 70)
        print(f"Test Results: {result.testsRun} tests run, {len(result.errors)} errors, {len(result.failures)} failures")
        print("=" * 70)

        # Return exit code based on test success
        return 0 if result.wasSuccessful() else 1

def run_specific_test(test_name, with_coverage=False):
    """Run a specific test module"""
    if not test_name.startswith('test_'):
        test_name = f'test_{test_name}'

    if not test_name.endswith('.py'):
        test_name = f'{test_name}.py'

    test_path = os.path.join(os.path.dirname(__file__), test_name)

    if not os.path.exists(test_path):
        print(f"Error: Test file {test_path} does not exist")
        return 1

    if PYTEST_AVAILABLE and with_coverage:
        print("=" * 70)
        print(f"Running tests from {test_name} with coverage")
        print("=" * 70)

        pytest_args = [
            '--cov=computerquest',
            '--cov-report=term',
            '--cov-report=html',
            test_path
        ]
        return pytest.main(pytest_args)
    else:
        # Load and run specific test
        module_name = os.path.splitext(test_name)[0]
        loader = unittest.TestLoader()

        try:
            # Import the module dynamically
            test_module = __import__(f'tests.{module_name}', fromlist=[''])
            test_suite = loader.loadTestsFromModule(test_module)

            # Run tests
            print("=" * 70)
            print(f"Running tests from {module_name}")
            print("=" * 70)

            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(test_suite)

            print("\n" + "=" * 70)
            print(f"Test Results: {result.testsRun} tests run, {len(result.errors)} errors, {len(result.failures)} failures")
            print("=" * 70)

            return 0 if result.wasSuccessful() else 1

        except ImportError as e:
            print(f"Error importing test module {module_name}: {e}")
            return 1

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="KodeKloud Computer Quest Test Runner")
    parser.add_argument("test_module", nargs="?", help="Specific test module to run (without test_ prefix)")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if args.coverage and not PYTEST_AVAILABLE:
        print("Coverage reporting requires pytest and pytest-cov to be installed.")
        print("Install with: pip install pytest pytest-cov")
        sys.exit(1)

    if args.test_module:
        # Run specific test module
        exit_code = run_specific_test(args.test_module, args.coverage)
    else:
        # Run all tests
        exit_code = run_all_tests(args.coverage)

    sys.exit(exit_code)
