"""Unit tests for app.utils.workers, using pytest-qt to drive the Qt event
loop needed for QThreadPool signals to be delivered.
"""

from __future__ import annotations

from app.utils.workers import run_async


def _add(a, b):
    return a + b


def _boom():
    raise RuntimeError("boom")


def test_run_async_delivers_result(qtbot):
    results = {}

    def on_result(value):
        results["value"] = value

    run_async(_add, 2, 3, on_result=on_result)

    qtbot.waitUntil(lambda: "value" in results, timeout=2000)
    assert results["value"] == 5


def test_run_async_delivers_error(qtbot):
    errors = {}

    def on_error(exc, tb):
        errors["exc"] = exc
        errors["tb"] = tb

    run_async(_boom, on_error=on_error)

    qtbot.waitUntil(lambda: "exc" in errors, timeout=2000)
    assert isinstance(errors["exc"], RuntimeError)
    assert "boom" in str(errors["exc"])


def test_run_async_calls_on_finished_regardless_of_outcome(qtbot):
    finished = {"count": 0}

    def on_finished():
        finished["count"] += 1

    run_async(_add, 1, 1, on_finished=on_finished)
    qtbot.waitUntil(lambda: finished["count"] == 1, timeout=2000)

    run_async(_boom, on_finished=on_finished, on_error=lambda *_: None)
    qtbot.waitUntil(lambda: finished["count"] == 2, timeout=2000)
