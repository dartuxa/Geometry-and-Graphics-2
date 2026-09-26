"""

Допоміжні функції для UI: конвертація numpy-масивів у Qt-зображення.

"""
from __future__ import annotations

import numpy as np
from PyQt5.QtGui import QImage, QPixmap


def numpy_rgb_to_qimage(img: np.ndarray) -> QImage:
    """
    img - (H, W, 3), значення float у [0, 1].
    Повертає QImage у форматі RGB888.
    """
    arr = np.clip(img, 0.0, 1.0)
    arr8 = (arr * 255.0 + 0.5).astype(np.uint8)
    arr8 = np.ascontiguousarray(arr8)
    h, w, _ = arr8.shape
    qimg = QImage(arr8.data, w, h, 3 * w, QImage.Format_RGB888)
    return qimg.copy()


def numpy_rgb_to_pixmap(img: np.ndarray) -> QPixmap:
    return QPixmap.fromImage(numpy_rgb_to_qimage(img))


def channel_to_qimage(channel: np.ndarray) -> QImage:
    """
    channel - 2D масив (H, W), довільний дійсний діапазон значень.
    Нормалізує канал (min-max) в [0, 255] і повертає grayscale QImage.
    """
    c = channel.astype(np.float64)
    cmin, cmax = float(c.min()), float(c.max())
    if cmax - cmin < 1e-12:
        norm = np.zeros_like(c)
    else:
        norm = (c - cmin) / (cmax - cmin)
    arr8 = (norm * 255.0 + 0.5).astype(np.uint8)
    arr8 = np.ascontiguousarray(arr8)
    h, w = arr8.shape
    qimg = QImage(arr8.data, w, h, w, QImage.Format_Grayscale8)
    return qimg.copy()


def channel_to_pixmap(channel: np.ndarray) -> QPixmap:
    return QPixmap.fromImage(channel_to_qimage(channel))
