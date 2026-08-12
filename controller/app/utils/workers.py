"""Runs a blocking callable (typically an `app/api` call) off the Qt main
thread via QThreadPool, reporting back through Qt signals. Every `services/`
method that touches the network uses this instead of calling `api/`
directly on the main thread.
"""

from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

logger = logging.getLogger("controller.utils.workers")

# QRunnable is not QObject-derived, so nothing pins a Worker's Python object
# (and therefore its `signals` QObject) alive once `run_async()` returns -
# QThreadPool.start() runs it asynchronously on another thread, and if the
# caller doesn't hold a reference (the common case: fire-and-forget calls),
# Python's GC can collect the Worker while it's still mid-flight, silently
# dropping its signal emissions. Keeping a strong reference here until the
# worker reports `finished` is the standard fix for this well-known
# PySide6/PyQt gotcha.
_active_workers: set["Worker"] = set()


class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(Exception, str)  # exception instance, formatted traceback
    result = Signal(object)


class Worker(QRunnable):
    """Wraps a callable for QThreadPool. Usage:

        worker = Worker(api_function, arg1, arg2, kwarg=value)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(on_error)
        thread_pool.start(worker)
    """

    def __init__(self, fn: Callable[..., Any], *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as error:  # noqa: BLE001 - intentionally broad, reported via signal
            logger.exception("Background task failed: %s", self.fn)
            self.signals.error.emit(error, traceback.format_exc())
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


def run_async(
    fn: Callable[..., Any],
    *args,
    on_result: Callable[[Any], None] | None = None,
    on_error: Callable[[Exception, str], None] | None = None,
    on_finished: Callable[[], None] | None = None,
    thread_pool: QThreadPool | None = None,
    **kwargs,
) -> Worker:
    """Convenience wrapper: fire-and-forget a background call with optional
    result/error/finished callbacks. Returns the Worker in case the caller
    wants to hold a reference (usually unnecessary - QThreadPool keeps it
    alive until it finishes).
    """

    pool = thread_pool or QThreadPool.globalInstance()
    worker = Worker(fn, *args, **kwargs)
    if on_result is not None:
        worker.signals.result.connect(on_result)
    if on_error is not None:
        worker.signals.error.connect(on_error)
    if on_finished is not None:
        worker.signals.finished.connect(on_finished)

    _active_workers.add(worker)
    worker.signals.finished.connect(lambda: _active_workers.discard(worker))

    pool.start(worker)
    return worker
