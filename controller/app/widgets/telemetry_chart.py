"""Rolling line-chart widget (pyqtgraph) used for CPU/RAM history on Device
Details. Telemetry only changes on each heartbeat (~30s default, see
docs/PHASE_1_ANALYSIS.md), so this is fed by DeviceDetailService's polling,
not a true realtime stream - the chart still reads as "live" to the
operator since points appear as they arrive.
"""

from __future__ import annotations

import time
from collections import deque

import pyqtgraph as pg

from app.theme import COLORS


class RollingLineChart(pg.PlotWidget):
    def __init__(self, title: str, y_label: str = "%", max_points: int = 60, y_max: float | None = 100, parent=None):
        super().__init__(parent)
        self.setBackground(COLORS.bg_surface)
        self.showGrid(x=True, y=True, alpha=0.15)
        self.setTitle(title, color=COLORS.text_secondary, size="10pt")
        self.setLabel("left", y_label, color=COLORS.text_muted)
        self.getAxis("left").setTextPen(COLORS.text_muted)
        self.getAxis("bottom").setTextPen(COLORS.text_muted)
        if y_max is not None:
            self.setYRange(0, y_max)
        self.hideAxis("bottom")

        self._max_points = max_points
        self._values: deque[float] = deque(maxlen=max_points)
        self._times: deque[float] = deque(maxlen=max_points)

        self._curve = self.plot(pen=pg.mkPen(color=COLORS.purple_light, width=2))

    def add_point(self, value: float | None) -> None:
        if value is None:
            return
        self._times.append(time.time())
        self._values.append(value)
        x = list(range(len(self._values)))
        self._curve.setData(x, list(self._values))

    def clear_points(self) -> None:
        self._values.clear()
        self._times.clear()
        self._curve.setData([], [])
