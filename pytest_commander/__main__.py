"""PyTest UI server main entry point."""
import argparse
import logging
import os
import subprocess
import sys
import webbrowser
from typing import Optional

from pytest_commander import api

LOGGER = logging.getLogger(__name__)

# Time to poll the HTTP server to be ready, in seconds.
POLL_TIME = 0.2


def main():
    """Start the server."""
    args = parse_args()
    if args.port == 0:
        sys.exit("Binding to port 0 is not currently supported.")

    log_level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=log_level)

    app, socketio, test_runner = api.build_app(args.directory, args.watch)
    address = f"http://{display_host(args.host)}:{args.port}/"

    if not args.no_browse:
        # According to the eventlet concurrency model, this will not be started
        # as a background task until the socketio server has started and
        # co-operatively yields control.
        socketio.start_background_task(open_webbrowser, address, args.browser)

    with test_runner:
        socketio.run(app, host=args.host, port=args.port)


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
        default=os.getcwd(),
        help=f"Directory to find PyTest test modules, defaults to cwd ({os.getcwd()})",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help=f"Host to bind to, defaults to localhost.",
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
        "-w",
        "--watch",
        choices=["collect", "autorun", "disabled"],
        default="collect",
        help=(
            "Filesystem watch mode. In the default 'collect' mode, tests are "
            "recollected after filesystem changes are detected but not "
            "automatically re-run. To re-run tests automatically when they are "
            "modified, use 'autorun' mode. To disable file-watching entirely, "
            "select 'disabled'."
        ),
    )
    parser.add_argument(
        "-b",
        "--browser",
        help=(
            "Specify web browser executable to open the UI in. If not specified, "
            "the system's default browser will be used."
        ),
    )

    return parser.parse_args()


def open_webbrowser(address: str, browser: Optional[str]):
    LOGGER.critical("View in your browser at %s", address)
    if browser:
        subprocess.Popen([browser, address])
    else:
        webbrowser.open(address)


if __name__ == "__main__":
    main()
