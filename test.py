#!/usr/bin/env python3
"""Run all tests."""
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(__file__)


def main():
    pipenv_exe = shutil.which("pipenv")
    if not pipenv_exe:
        sys.exit("Pipenv is required, please ensure it is installed and on your PATH.")

    print("Running mypy type checker...")
    subprocess.check_call(
        [pipenv_exe, "run", "mypy", os.path.join(REPO_ROOT, "pytest_commander")]
    )

    print("Running python unit tests...")
    subprocess.check_call(
        [pipenv_exe, "run", "pytest", os.path.join(REPO_ROOT, "tests")]
    )

    print("Success! All tests passed.")


if __name__ == "__main__":
    main()
