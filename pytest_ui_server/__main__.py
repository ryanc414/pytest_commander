"""PyTest UI server main entry point."""
import argparse
import logging
import sys

from pytest_ui_server import api

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Start the server."""
    args = parse_args()
    app, socketio = api.build_app(args.directory)
    LOGGER.critical(f"View in your browser at http://localhost:{args.port}/")
    socketio.run(app, port=args.port)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line args."""
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("-p", "--port", type=int, default=5000)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
