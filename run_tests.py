#!/usr/bin/env python3
"""
Test runner script for AI Document Compliance Checker.
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*50)
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ SUCCESS")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ FAILED")
        if result.stderr:
            print(result.stderr)
        if result.stdout:
            print(result.stdout)
        return False
    
    return True


def main():
    """Main test runner function."""
    print("🧪 AI Document Compliance Checker - Test Suite")
    print("="*60)
    
    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Run linting
    print("\n🔍 Running code linting...")
    lint_success = run_command(
        "python -m flake8 app tests --max-line-length=100 --ignore=E501,W503",
        "Code linting with flake8"
    )
    
    # Run unit tests
    print("\n🧪 Running unit tests...")
    unit_success = run_command(
        "python -m pytest tests/ -v -m 'not integration' --cov=app --cov-report=term-missing",
        "Unit tests with coverage"
    )
    
    # Run integration tests
    print("\n🔗 Running integration tests...")
    integration_success = run_command(
        "python -m pytest tests/ -v -m integration",
        "Integration tests"
    )
    
    # Run all tests
    print("\n🎯 Running complete test suite...")
    all_tests_success = run_command(
        "python -m pytest tests/ -v --cov=app --cov-report=html",
        "Complete test suite with HTML coverage report"
    )
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    results = [
        ("Code Linting", lint_success),
        ("Unit Tests", unit_success),
        ("Integration Tests", integration_success),
        ("Complete Test Suite", all_tests_success)
    ]
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if not success:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All tests passed! The application is ready for deployment.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please fix the issues before deployment.")
        sys.exit(1)


if __name__ == "__main__":
    main()
