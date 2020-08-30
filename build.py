#!/usr/bin/env python3
"""
Build everything from source.

Handles:
1. Install npm dependencies and build the UI client
2. Build source and binary distributions of the python package.
"""
import os
import shutil
import subprocess
import sys


WEB_CLIENT_DIR = os.path.join(
    os.path.dirname(__file__), "pytest_commander", "web_client"
)


def main():
    npm_exe = shutil.which("npm")
    if not npm_exe:
        sys.exit(
            "Error, could not find npm installation. Ensure that npm is "
            "installed and on your PATH."
        )

    pipenv_exe = shutil.which("pipenv")
    if not pipenv_exe:
        sys.exit("Pipenv is required, please ensure it is installed and on your PATH.")

    print("Building UI...")
    subprocess.check_call([npm_exe, "install"], cwd=WEB_CLIENT_DIR)
    subprocess.check_call([npm_exe, "run", "build"], cwd=WEB_CLIENT_DIR)

    print("Done! Find source archive and wheel under dist/")
    print("Run tests with: $ python test.py")


if __name__ == "__main__":
    main()
