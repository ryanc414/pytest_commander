"""PyTest UI server main entry point."""
import argparse
import logging
import os
import sys
import webbrowser
import time

from pytest_web_ui import api

LOGGER = logging.getLogger(__name__)


def main():
    """Start the server."""
    args = parse_args()
    if args.port == 0:
        sys.exit("Binding to port 0 is not currently supported.")

    log_level = logging.DEBUG if args.debug else logging.CRITICAL
    logging.basicConfig(level=log_level)

    app, socketio = api.build_app(args.directory)
    address = f"http://localhost:{args.port}/"
    LOGGER.critical(f"View in your browser at {address}")

    if not args.no_browse:
        webbrowser.open(address)

    socketio.run(app, port=args.port, debug=args.debug)


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
    parser.add_argument(
        "--no-browse",
        action="store_true",
        help="Do not automatically open a web browser to view the UI",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
