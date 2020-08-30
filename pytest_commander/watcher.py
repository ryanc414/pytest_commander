"""
Watch for filesystem events in the background. Watchdog is not compatible
with the eventlet concurrency model so this needs to run in a separate OS
thread or process.
"""
import logging
import multiprocessing
import os
import time
from typing import Callable

from watchdog import events  # type: ignore
from watchdog import observers  # type: ignore

LOGGER = logging.getLogger(__name__)
READY = 0xFEED


def watch_filesystem(root_dir: str, events_queue: multiprocessing.Queue):
    event_handler = FileSystemEventHandler(events_queue)
    observer = observers.Observer()
    observer.schedule(event_handler, root_dir, recursive=True)
    observer.start()
    events_queue.put(READY)
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
        self._events_queue.put(event)
