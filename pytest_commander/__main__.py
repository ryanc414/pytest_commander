"""PyTest UI server main entry point."""
import argparse
import logging
import threading
import os
import sys
import webbrowser
import time

import eventlet  # type: ignore
import requests
from pytest_commander import api

LOGGER = logging.getLogger(__name__)

# Time to poll the HTTP server to be ready, in seconds.
POLL_TIME = 0.2


def main():
    """Start the server."""
    args = parse_args()
    if args.port == 0:
        sys.exit("Binding to port 0 is not currently supported.")

    log_level = logging.DEBUG if args.debug else logging.CRITICAL
    logging.basicConfig(level=log_level)

    app, socketio, test_runner = api.build_app(args.directory, not args.no_watch)
    address = f"http://{display_host(args.host)}:{args.port}/"
    LOGGER.critical(f"View in your browser at {address}")

    if not args.no_browse:
        threading.Thread(target=open_webbrowser, args=(address,)).start()

    with test_runner:
        socketio.run(app, host=args.host, port=args.port, debug=args.debug)


def display_host(host: str) -> str:
    """For the special zero IPv4/6 addresses, return localhost for access."""
    if host == "0.0.0.0" or host == "::":
        return "localhost"
    return host


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
        "--host", default="localhost", help=f"Host to bind to, defaults to localhost.",
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
    parser.add_argument(
        "--no-watch",
        action="store_true",
        help="Disable watching for filesystem changes in the background",
    )

    return parser.parse_args()


def open_webbrowser(address: str):
    """Wait for the server to be ready, then open the app in the webbrowser."""
    status_code = None
    while status_code != 200:
        try:
            rsp = requests.get(address)
            status_code = rsp.status_code
        except requests.ConnectionError:
            pass
        time.sleep(0.1)

    webbrowser.open(address)


if __name__ == "__main__":
    main()
