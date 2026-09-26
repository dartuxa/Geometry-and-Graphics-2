"""
Побудова гістограм колірних каналів.

Гістограми будуються для RGB-подання зображення (джерело / ціль / результат),
незалежно від того, в якому просторі відбувалась корекція.
"""
from __future__ import annotations

import numpy as np


def compute_histogram(
    channel: np.ndarray,
    bins: int = 256,
    value_range: tuple[float, float] = (0.0, 1.0),
) -> np.ndarray:
    """
    channel -- 2D масив (H, W) значень одного каналу.
    Повертає масив довжини `bins` - кількість пікселів у кожному "кошику".
    """
    hist, _ = np.histogram(channel, bins=bins, range=value_range)
    return hist


def compute_rgb_histograms(img_rgb: np.ndarray, bins: int = 256) -> dict[str, np.ndarray]:
    """Гістограми одразу для R, G, B каналів RGB-зображення (значення [0,1])."""
    return {
        "R": compute_histogram(img_rgb[..., 0], bins=bins),
        "G": compute_histogram(img_rgb[..., 1], bins=bins),
        "B": compute_histogram(img_rgb[..., 2], bins=bins),
    }


def compute_space_histograms(
    img: np.ndarray,
    channel_names: tuple[str, str, str],
    bins: int = 64,
) -> dict[str, tuple[np.ndarray, tuple[float, float]]]:
    """
    Гістограми для довільного колірного простору (Lab/HSL/HSV/YIQ/RGB).

    На відміну від compute_rgb_histograms, діапазон значень для кожного
    каналу визначається за фактичними даними (min/max), бо, наприклад,
    канали a, b в Lab не обмежені [0, 1].

    Повертає {назва_каналу: (гістограма, (min, max))}.
    """
    result = {}
    for i, name in enumerate(channel_names):
        channel = img[..., i]
        cmin, cmax = float(channel.min()), float(channel.max())
        if cmax - cmin < 1e-9:
            cmax = cmin + 1e-9
        hist = compute_histogram(channel, bins=bins, value_range=(cmin, cmax))
        result[name] = (hist, (cmin, cmax))
    return result