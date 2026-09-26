"""

Одна колонка інтерфейсу: зображення + канали + гістограма.
Використовується тричі - для джерела, цілі та результату.

"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from .image_panel import ImagePanel
from .channel_view import ChannelRow
from .histogram_view import HistogramView


class ImageColumn(QWidget):
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.image_panel = ImagePanel(title)
        self.channel_row = ChannelRow()
        self.histogram_view = HistogramView()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.image_panel, stretch=3)
        layout.addWidget(self.channel_row)
        layout.addWidget(self.histogram_view, stretch=1)

    def update_content(
        self,
        rgb_image: Optional[np.ndarray],
        space_image: Optional[np.ndarray],
        channel_names: tuple[str, str, str],
    ) -> None:
        self.image_panel.set_image(rgb_image)
        self.channel_row.set_channels(space_image, channel_names)
        self.histogram_view.set_image(space_image, channel_names)