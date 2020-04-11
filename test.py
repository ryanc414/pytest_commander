#!/usr/bin/env python3
"""Run all tests."""
import os
import subprocess

REPO_ROOT = os.path.dirname(__file__)


def main():
    print("Running mypy type checkker...")
    subprocess.check_call(
        ["pipenv", "run", "mypy", os.path.join(REPO_ROOT, "pytest_web_ui")]
    )

    print("Running python unit tests...")
    subprocess.check_call(["pipenv", "run", "pytest", os.path.join(REPO_ROOT, "tests")])

    print("Success! All tests passed.")


if __name__ == "__main__":
    main()
