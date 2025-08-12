#!/usr/bin/env python3
"""
Test runner for CTX-CARD generator.

This script provides convenient ways to run the test suite with different configurations.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print(f"\n✅ {description} completed successfully")
        return True
    else:
        print(f"\n❌ {description} failed with return code {result.returncode}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run CTX-CARD generator tests")
    parser.add_argument(
        "--unit", action="store_true",
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration", action="store_true",
        help="Run integration tests only"
    )
    parser.add_argument(
        "--cli", action="store_true",
        help="Run CLI tests only"
    )
    parser.add_argument(
        "--fast", action="store_true",
        help="Run fast tests only (skip slow tests)"
    )
    parser.add_argument(
        "--coverage", action="store_true",
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--format", action="store_true",
        help="Run code formatting checks"
    )
    parser.add_argument(
        "--lint", action="store_true",
        help="Run linting checks"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all checks (tests, format, lint)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Determine what to run
    if args.all:
        run_format = True
        run_lint = True
        run_tests = True
    else:
        run_format = args.format
        run_lint = args.lint
        run_tests = not (args.format or args.lint)  # Default to tests if no specific option
    
    success = True
    
    # Run code formatting
    if run_format:
        print("\n🔧 Running code formatting checks...")
        
        # Check if Black is available
        try:
            import black
            if not run_command([sys.executable, "-m", "black", "--check", "src/", "tests/"], "Black formatting check"):
                success = False
        except ImportError:
            print("⚠️  Black not available, skipping formatting check")
        
        # Check if isort is available
        try:
            import isort
            if not run_command([sys.executable, "-m", "isort", "--check-only", "src/", "tests/"], "Import sorting check"):
                success = False
        except ImportError:
            print("⚠️  isort not available, skipping import sorting check")
    
    # Run linting
    if run_lint:
        print("\n🔍 Running linting checks...")
        
        # Check if flake8 is available
        try:
            import flake8
            if not run_command([sys.executable, "-m", "flake8", "src/", "tests/"], "Flake8 linting"):
                success = False
        except ImportError:
            print("⚠️  flake8 not available, skipping linting check")
    
    # Run tests
    if run_tests:
        print("\n🧪 Running tests...")
        
        # Build pytest command
        pytest_cmd = [sys.executable, "-m", "pytest"]
        
        if args.verbose:
            pytest_cmd.append("-v")
        
        if args.coverage:
            pytest_cmd.extend(["--cov=src/ctxcard_gen", "--cov-report=term-missing"])
        
        # Add test selection
        if args.unit:
            pytest_cmd.extend(["-m", "unit"])
        elif args.integration:
            pytest_cmd.extend(["-m", "integration"])
        elif args.cli:
            pytest_cmd.extend(["-m", "cli"])
        elif args.fast:
            pytest_cmd.extend(["-m", "not slow"])
        
        if not run_command(pytest_cmd, "Pytest test suite"):
            success = False
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("🎉 All checks completed successfully!")
        sys.exit(0)
    else:
        print("💥 Some checks failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
