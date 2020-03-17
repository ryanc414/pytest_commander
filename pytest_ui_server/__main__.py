"""PyTest UI server main entry point."""
import argparse
import logging
import sys

from pytest_ui_server import api

logging.basicConfig(level=logging.DEBUG)


def main() -> int:
    """Start the server."""
    args = parse_args()
    app, socketio = api.build_app(args.directory)
    socketio.run(app)


def parse_args() -> argparse.Namespace:
    """Parse command-line args."""
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
