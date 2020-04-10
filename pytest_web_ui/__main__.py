"""PyTest UI server main entry point."""
import argparse
import logging
import os
import sys

from pytest_web_ui import api

LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Start the server."""
    args = parse_args()

    log_level = logging.DEBUG if args.debug else logging.CRITICAL
    logging.basicConfig(level=log_level)

    app, socketio = api.build_app(args.directory)
    LOGGER.critical(f"View in your browser at http://localhost:{args.port}/")
    socketio.run(app, port=args.port, debug=args.debug)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line args."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help=f"Directory to find PyTest test modules, defaults to cwd ({os.getcwd()})",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=5000,
        help="Port number to bind to, defaults to 5000",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug logging and use the debug web server",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
