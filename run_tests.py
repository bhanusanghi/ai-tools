#!/usr/bin/env python3
"""
Test runner for the divergence scanner
Runs both unit tests and integration tests
"""
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def run_unit_tests():
    """Run unit tests (fast, no network required)"""
    print("\n" + "=" * 60)
    print("Running Unit Tests")
    print("=" * 60 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Load unit tests
    suite.addTests(loader.discover('tests', pattern='test_indicators.py'))
    suite.addTests(loader.discover('tests', pattern='test_divergence.py'))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_integration_tests():
    """Run integration tests (slower, requires network)"""
    print("\n" + "=" * 60)
    print("Running Integration Tests (Real-Time Data)")
    print("=" * 60)
    print("\nNote: These tests fetch real data and may take a few minutes.")
    print("=" * 60 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Load integration tests
    suite.addTests(loader.discover('tests', pattern='test_integration.py'))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description='Run tests for Stock Divergence Scanner')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--all', action='store_true', default=True, help='Run all tests (default)')

    args = parser.parse_args()

    results = []

    # Determine which tests to run
    if args.unit or (not args.integration and args.all):
        results.append(('Unit Tests', run_unit_tests()))

    if args.integration or (not args.unit and args.all):
        results.append(('Integration Tests', run_integration_tests()))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Suite Summary")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All tests passed!\n")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the output above.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
