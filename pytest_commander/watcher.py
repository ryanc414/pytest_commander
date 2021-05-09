"""
Watch for filesystem events in the background. Watchdog is not compatible
with the eventlet concurrency model so this needs to run in a separate OS
thread or process.
"""
import logging
import multiprocessing
import os
import time
import traceback
from typing import Callable

from watchdog import events  # type: ignore
from watchdog import observers  # type: ignore

LOGGER = logging.getLogger(__name__)
READY = 0xFEED


def watch_filesystem(
    root_dir: str, events_queue: multiprocessing.Queue, log_level: int
):
    logging.basicConfig(level=log_level)
    LOGGER.debug("initiating filesystem watcher")
    try:
        _watch_filesystem(root_dir, events_queue)
    except Exception:
        traceback.print_exc()
        raise


def _watch_filesystem(root_dir: str, events_queue: multiprocessing.Queue):
    event_handler = FileSystemEventHandler(events_queue)
    observer = observers.Observer()
    observer.schedule(event_handler, root_dir, recursive=True)
    observer.start()
    events_queue.put(READY)
    LOGGER.debug("filesystem watcher is ready")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


class FileSystemEventHandler(events.FileSystemEventHandler):
    """Handles file system events."""

    def __init__(self, events_queue: multiprocessing.Queue):
        self._events_queue = events_queue

    def on_any_event(self, event: events.FileSystemEvent):
        LOGGER.debug("caught filesystem event %s", event)
        self._events_queue.put(event)
