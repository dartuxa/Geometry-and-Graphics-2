"""
Завантаження та збереження BMP-зображень.

Працюємо тільки з непалітровими (24-бітними) BMP.
Усі зображення в програмі представлені як numpy-масив (H, W, 3),
dtype=float64, значення компонент у діапазоні [0, 1].
"""
from __future__ import annotations

import numpy as np
from PIL import Image


class BMPLoadError(Exception):
    """Помилка завантаження BMP-файлу (не BMP, палітровий формат тощо)."""


def load_bmp(path: str) -> np.ndarray:
    """
    Завантажує 24-бітний BMP-файл.

    Повертає numpy-масив (H, W, 3), dtype=float64, значення в [0, 1].
    """
    img = Image.open(path)

    if img.format != "BMP":
        raise BMPLoadError(f"Файл '{path}' не є BMP-зображенням (формат: {img.format}).")

    if img.mode == "P":
        raise BMPLoadError(
            "Палітрові (indexed) BMP не підтримуються. "
            "За умовою лабораторної потрібне 24-бітне (непалітрове) зображення."
        )

    img = img.convert("RGB")  # гарантує рівно 3 канали, 8 біт на канал
    arr = np.asarray(img, dtype=np.float64) / 255.0
    return arr


def save_bmp(path: str, img: np.ndarray) -> None:
    """Зберігає масив (H, W, 3), значення [0, 1], як 24-бітний BMP."""
    arr = np.clip(img, 0.0, 1.0)
    arr = (arr * 255.0 + 0.5).astype(np.uint8)
    Image.fromarray(arr, mode="RGB").save(path, format="BMP")