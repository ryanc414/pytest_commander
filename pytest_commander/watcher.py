"""
Watch for filesystem events in the background. Watchdog is not compatible
with the eventlet concurrency model so this needs to run in a separate OS
thread or process.
"""
import logging
import multiprocessing
import time
from typing import Callable

from watchdog import events
from watchdog import observers

LOGGER = logging.getLogger(__name__)


def watch_filesystem(root_dir: str, events_queue: multiprocessing.Queue):
    event_handler = FileSystemEventHandler(events_queue)
    observer = observers.Observer()
    observer.schedule(event_handler, root_dir, recursive=True)
    observer.start()
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
        LOGGER.critical("*** handling filesystem event: %s", event)
        self._events_queue.put(event)
