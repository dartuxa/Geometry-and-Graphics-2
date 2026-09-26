"""

Побудова масок для виділення ділянки зображення.

"""
from __future__ import annotations

import numpy as np


def rectangle_mask(shape: tuple[int, int], x0: int, y0: int, x1: int, y1: int) -> np.ndarray:
    """
    shape - (H, W) розмір зображення.
    (x0, y0), (x1, y1) - протилежні кути прямокутника в пікселях
    (порядок кутів не важливий - координати автоматично сортуються).
    """
    h, w = shape
    x_min, x_max = sorted((int(x0), int(x1)))
    y_min, y_max = sorted((int(y0), int(y1)))
    x_min, x_max = int(np.clip(x_min, 0, w)), int(np.clip(x_max, 0, w))
    y_min, y_max = int(np.clip(y_min, 0, h)), int(np.clip(y_max, 0, h))

    mask = np.zeros((h, w), dtype=bool)
    mask[y_min:y_max, x_min:x_max] = True
    return mask


def circle_mask(shape: tuple[int, int], cx: int, cy: int, radius: int) -> np.ndarray:
    """
    shape - (H, W) розмір зображення.
    (cx, cy) - центр кола в пікселях, radius - радіус у пікселях.
    """
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2


def union_mask(*masks: np.ndarray) -> np.ndarray:
    """Об'єднання декількох масок (кілька мазків пензликом підряд)."""
    result = masks[0].copy()
    for m in masks[1:]:
        result |= m
    return result