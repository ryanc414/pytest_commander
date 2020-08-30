"""Utilities to help with using eventlet."""

import multiprocessing
import queue

import eventlet  # type: ignore

_ACTIVE_LOOP_SLEEP = 0.1  # seconds


def get_queue_noblock(q: multiprocessing.Queue):
    """
    Receive from a multiprocessing.Queue object without blocking from an
    eventlet green thread. Polls the queue and calls eventlet.sleep() to yield
    to other threads in between.
    """
    while True:
        try:
            return q.get_nowait()
        except queue.Empty:
            eventlet.sleep(_ACTIVE_LOOP_SLEEP)