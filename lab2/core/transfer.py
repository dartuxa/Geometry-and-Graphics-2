"""
Статистична корекція кольору (color transfer) - основний алгоритм.

Ідея:
  1. Перевести source і target у робочий колірний простір.
  2. Для кожного каналу порахувати математичне очікування E і дисперсію D.
  3. Кожен піксель target перетворити за формулою:
         p' = (p - E_t) * sqrt(D_s / D_t) + E_s
  4. Перевести результат назад у RGB.

Підтримується:
  - будь-який простір з colorspaces.CONVERTERS;
  - вибір, які саме канали коригувати;
  - маска ділянки, до якої застосовується корекція.
"""
from __future__ import annotations

import numpy as np

from .colorspaces import CONVERTERS


def channel_stats(img: np.ndarray, mask: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """
    Обчислює математичне очікування (E) і дисперсію (D) для кожного з 3 каналів.

    img  - масив (H, W, 3) у довільному колірному просторі.
    mask - булевий масив (H, W); 
        True = піксель враховується у статистиці.
        None = враховується все зображення.

    Повертає (E, D) - по масиву довжини 3 кожен.
    """
    if mask is None:
        pixels = img.reshape(-1, 3)
    else:
        pixels = img[mask]

    if pixels.size == 0:
        raise ValueError("Порожня ділянка: маска не виділяє жодного пікселя.")

    e = pixels.mean(axis=0)
    d = pixels.var(axis=0)
    return e, d


def apply_color_transfer(
    source_rgb: np.ndarray,
    target_rgb: np.ndarray,
    space: str = "Lab",
    channels: tuple[bool, bool, bool] = (True, True, True),
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    Переносить статистику кольору з source на target.

    source_rgb, target_rgb - (H, W, 3), значення [0, 1].
    space     - назва простору з colorspaces.CONVERTERS ("Lab", "HSL", "HSV", "YIQ").
    channels  - які з 3 каналів обраного простору коригувати (True/False кожен).
    mask      - маска (H, W) ділянки TARGET, до якої застосовується корекція.
                 Статистика джерела (E_s, D_s) завжди рахується по всьому
                 source-зображенню; статистика цілі (E_t, D_t) - тільки
                 по виділеній ділянці, якщо маска задана.

    Повертає результат у RGB, (H, W, 3), значення [0, 1].
    """
    if space not in CONVERTERS:
        raise ValueError(f"Невідомий колірний простір: {space!r}. Доступні: {list(CONVERTERS)}")

    to_space, from_space = CONVERTERS[space]

    src = to_space(source_rgb)
    tgt = to_space(target_rgb)

    e_s, d_s = channel_stats(src)
    e_t, d_t = channel_stats(tgt, mask=mask)

    result = tgt.copy()
    region = np.ones(tgt.shape[:2], dtype=bool) if mask is None else mask

    for c in range(3):
        if not channels[c]:
            continue
        std_ratio = np.sqrt(d_s[c] / d_t[c]) if d_t[c] > 1e-12 else 1.0
        channel = tgt[..., c]
        transformed = (channel - e_t[c]) * std_ratio + e_s[c]
        result[..., c] = np.where(region, transformed, channel)

    return from_space(result)