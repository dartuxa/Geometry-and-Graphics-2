"""

Показ окремих каналів зображення - кожен канал як окреме grayscale зображення.

"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout

from .utils import channel_to_pixmap

_THUMB_SIZE = 100


class ChannelRow(QWidget):
    """Рядок з трьома мініатюрами - по одній на кожен канал колірного простору."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._name_labels: list[QLabel] = []
        self._image_labels: list[QLabel] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        for _ in range(3):
            col = QVBoxLayout()
            name_lbl = QLabel("-")
            name_lbl.setAlignment(Qt.AlignCenter)
            img_lbl = QLabel()
            img_lbl.setAlignment(Qt.AlignCenter)
            img_lbl.setFixedSize(_THUMB_SIZE, _THUMB_SIZE)
            img_lbl.setStyleSheet("border: 1px solid #666; background: #202020;")
            col.addWidget(name_lbl)
            col.addWidget(img_lbl)
            layout.addLayout(col)
            self._name_labels.append(name_lbl)
            self._image_labels.append(img_lbl)

    def set_channels(
        self,
        space_img: Optional[np.ndarray],
        channel_names: tuple[str, str, str],
    ) -> None:
        """
        space_img - (H, W, 3) зображення у робочому колірному просторі, або None.
        channel_names - підписи для 3 каналів (наприклад ("L", "a", "b")).
        """
        for i in range(3):
            self._name_labels[i].setText(channel_names[i])
            if space_img is None:
                self._image_labels[i].clear()
                continue
            pixmap = channel_to_pixmap(space_img[..., i])
            scaled = pixmap.scaled(
                _THUMB_SIZE, _THUMB_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self._image_labels[i].setPixmap(scaled)