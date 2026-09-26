"""

Гістограми колірних каналів одного зображення (matplotlib, вбудований у Qt).

"""
from __future__ import annotations

from typing import Optional

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core.histogram import compute_space_histograms

_CHANNEL_COLORS = ("#e74c3c", "#2ecc71", "#3498db") # для 1-го/2-го/3-го каналу


class HistogramView(FigureCanvas):
    """Гістограми трьох каналів одного зображення, накладені на один графік."""

    def __init__(self, parent=None, bins: int = 64):
        self.bins = bins
        fig = Figure(figsize=(3.0, 1.7), tight_layout=True)
        super().__init__(fig)
        if parent is not None:
            self.setParent(parent)
        self.ax = fig.add_subplot(111)
        self._style_axes()

    def _style_axes(self) -> None:
        self.ax.set_facecolor("#1e1e1e")
        self.figure.set_facecolor("#1e1e1e")
        self.ax.tick_params(colors="#cccccc", labelsize=6)
        for spine in self.ax.spines.values():
            spine.set_color("#555555")

    def set_image(self, space_img: Optional[np.ndarray], channel_names: tuple[str, str, str]) -> None:
        self.ax.clear()
        self._style_axes()

        if space_img is not None:
            hists = compute_space_histograms(space_img, channel_names, bins=self.bins)
            for i, name in enumerate(channel_names):
                hist, (cmin, cmax) = hists[name]
                xs = np.linspace(cmin, cmax, self.bins)
                self.ax.plot(xs, hist, color=_CHANNEL_COLORS[i], linewidth=1, label=name)
            self.ax.legend(fontsize=6, facecolor="#2a2a2a", labelcolor="#dddddd")

        self.draw_idle()