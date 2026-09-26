"""
Перетворення між колірними просторами.

Усі функції приймають/повертають numpy-масив (H, W, 3) типу float64.
Для RGB, HSL(частково), HSV, YIQ і Lab компоненти масштабовані так, як
зручно для роботи (H у HSL/HSV в градусах 0..360, решта компонент - довільний
дійсний діапазон для Lab/YIQ, [0,1] для RGB/S/L/V).

Простір Lab реалізовано за методом Rudermann (RGB -> LMS -> log -> Lab):
  - перед логарифмуванням компоненти RGB обрізаються знизу до 3/255,
    щоб уникнути log(0);
  - перед переходом у LMS усі компоненти масштабуються так, щоб білому
    відповідало ~235/255 (0.92157) - це уникає виходу результату
    за межі допустимих значень після зворотного переходу;
  - при зворотному переході з Lab у RGB масштаб відновлюється.
"""
from __future__ import annotations

import numpy as np



_RGB2LMS = np.array([
    [0.3811, 0.5783, 0.0402],
    [0.1967, 0.7244, 0.0782],
    [0.0241, 0.1288, 0.8444],
])
_LMS2RGB = np.linalg.inv(_RGB2LMS)

_SQRT3, _SQRT6, _SQRT2 = np.sqrt(3.0), np.sqrt(6.0), np.sqrt(2.0)

_MIN_VALUE = 3.0 / 255.0
_WHITE_SCALE = 235.0 / 255.0


def _apply_matrix(img: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Множить кожен піксель (вектор з 3 компонент) на матрицю 3x3."""
    h, w, _ = img.shape
    flat = img.reshape(-1, 3)
    out = flat @ matrix.T
    return out.reshape(h, w, 3)


def rgb_to_lab(img: np.ndarray) -> np.ndarray:
    """RGB [0,1] -> Ruderman Lab."""
    rgb = np.clip(img, _MIN_VALUE, 1.0)
    rgb = rgb * _WHITE_SCALE

    lms = _apply_matrix(rgb, _RGB2LMS)
    lms = np.clip(lms, 1e-6, None)
    log_lms = np.log(lms)

    l_ = (log_lms[..., 0] + log_lms[..., 1] + log_lms[..., 2]) / _SQRT3
    a_ = (log_lms[..., 0] + log_lms[..., 1] - 2 * log_lms[..., 2]) / _SQRT6
    b_ = (log_lms[..., 0] - log_lms[..., 1]) / _SQRT2

    return np.stack([l_, a_, b_], axis=-1)


def lab_to_rgb(lab: np.ndarray) -> np.ndarray:
    """Ruderman Lab -> RGB [0,1]."""
    l_, a_, b_ = lab[..., 0], lab[..., 1], lab[..., 2]

    log_l = l_ / _SQRT3 + a_ / _SQRT6 + b_ / _SQRT2
    log_m = l_ / _SQRT3 + a_ / _SQRT6 - b_ / _SQRT2
    log_s = l_ / _SQRT3 - 2 * a_ / _SQRT6

    log_lms = np.stack([log_l, log_m, log_s], axis=-1)
    lms = np.exp(log_lms)

    rgb = _apply_matrix(lms, _LMS2RGB)
    rgb = rgb / _WHITE_SCALE
    return np.clip(rgb, 0.0, 1.0)



def rgb_to_hsl(img: np.ndarray) -> np.ndarray:
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    maxc = np.max(img, axis=-1)
    minc = np.min(img, axis=-1)
    delta = maxc - minc

    l_ = (maxc + minc) / 2.0

    s_ = np.zeros_like(l_)
    mid = (l_ > 0) & (l_ < 1)
    denom = np.where(l_ < 0.5, 2 * l_, 2 - 2 * l_)
    np.divide(delta, denom, out=s_, where=mid & (denom != 0))

    h_ = np.zeros_like(l_)
    nz = delta > 0
    cond_r = nz & (maxc == r) & (maxc != g)
    cond_g = nz & (maxc == g) & (maxc != b)
    cond_b = nz & (maxc == b) & (maxc != r)

    h_[cond_r] += (g[cond_r] - b[cond_r]) / delta[cond_r]
    h_[cond_g] += 2 + (b[cond_g] - r[cond_g]) / delta[cond_g]
    h_[cond_b] += 4 + (r[cond_b] - g[cond_b]) / delta[cond_b]
    h_ *= 60.0
    h_ = np.mod(h_, 360.0)

    return np.stack([h_, s_, l_], axis=-1)


def hsl_to_rgb(hsl: np.ndarray) -> np.ndarray:
    h_ = np.mod(hsl[..., 0], 360.0)
    s_, l_ = hsl[..., 1], hsl[..., 2]

    sat_r = np.zeros_like(h_)
    sat_g = np.zeros_like(h_)
    sat_b = np.zeros_like(h_)

    m1 = h_ < 120
    m2 = (h_ >= 120) & (h_ < 240)
    m3 = h_ >= 240

    sat_r[m1] = (120 - h_[m1]) / 60.0
    sat_g[m1] = h_[m1] / 60.0

    sat_g[m2] = (240 - h_[m2]) / 60.0
    sat_b[m2] = (h_[m2] - 120) / 60.0

    sat_r[m3] = (h_[m3] - 240) / 60.0
    sat_b[m3] = (360 - h_[m3]) / 60.0

    sat_r = np.clip(sat_r, 0, 1)
    sat_g = np.clip(sat_g, 0, 1)
    sat_b = np.clip(sat_b, 0, 1)

    ctmp_r = 2 * s_ * sat_r + (1 - s_)
    ctmp_g = 2 * s_ * sat_g + (1 - s_)
    ctmp_b = 2 * s_ * sat_b + (1 - s_)

    low = l_ < 0.5
    r = np.where(low, l_ * ctmp_r, (1 - l_) * ctmp_r + 2 * l_ - 1)
    g = np.where(low, l_ * ctmp_g, (1 - l_) * ctmp_g + 2 * l_ - 1)
    b = np.where(low, l_ * ctmp_b, (1 - l_) * ctmp_b + 2 * l_ - 1)

    return np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)



def rgb_to_hsv(img: np.ndarray) -> np.ndarray:
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    maxc = np.max(img, axis=-1)
    minc = np.min(img, axis=-1)
    delta = maxc - minc

    v_ = maxc
    s_ = np.divide(delta, maxc, out=np.zeros_like(maxc), where=maxc > 0)

    h_ = np.zeros_like(v_)
    nz = delta > 0
    cond_r = nz & (maxc == r) & (maxc != g)
    cond_g = nz & (maxc == g) & (maxc != b)
    cond_b = nz & (maxc == b) & (maxc != r)

    h_[cond_r] += (g[cond_r] - b[cond_r]) / delta[cond_r]
    h_[cond_g] += 2 + (b[cond_g] - r[cond_g]) / delta[cond_g]
    h_[cond_b] += 4 + (r[cond_b] - g[cond_b]) / delta[cond_b]
    h_ *= 60.0
    h_ = np.mod(h_, 360.0)

    return np.stack([h_, s_, v_], axis=-1)


def hsv_to_rgb(hsv: np.ndarray) -> np.ndarray:
    h_ = np.mod(hsv[..., 0], 360.0)
    s_, v_ = hsv[..., 1], hsv[..., 2]

    sat_r = np.zeros_like(h_)
    sat_g = np.zeros_like(h_)
    sat_b = np.zeros_like(h_)

    m1 = h_ < 120
    m2 = (h_ >= 120) & (h_ < 240)
    m3 = h_ >= 240

    sat_r[m1] = (120 - h_[m1]) / 60.0
    sat_g[m1] = h_[m1] / 60.0

    sat_g[m2] = (240 - h_[m2]) / 60.0
    sat_b[m2] = (h_[m2] - 120) / 60.0

    sat_r[m3] = (h_[m3] - 240) / 60.0
    sat_b[m3] = (360 - h_[m3]) / 60.0

    sat_r = np.clip(sat_r, 0, 1)
    sat_g = np.clip(sat_g, 0, 1)
    sat_b = np.clip(sat_b, 0, 1)

    r = (1 - s_ + s_ * sat_r) * v_
    g = (1 - s_ + s_ * sat_g) * v_
    b = (1 - s_ + s_ * sat_b) * v_

    return np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)



_RGB2YIQ = np.array([
    [0.299, 0.587, 0.114],
    [0.596, -0.275, -0.321],
    [0.212, -0.528, 0.311],
])
_YIQ2RGB = np.array([
    [1.0, 0.956, 0.621],
    [1.0, -0.272, -0.647],
    [1.0, -1.106, -1.703],
])


def rgb_to_yiq(img: np.ndarray) -> np.ndarray:
    return _apply_matrix(img, _RGB2YIQ)


def yiq_to_rgb(yiq: np.ndarray) -> np.ndarray:
    rgb = _apply_matrix(yiq, _YIQ2RGB)
    return np.clip(rgb, 0.0, 1.0)



CONVERTERS = {
    "Lab": (rgb_to_lab, lab_to_rgb),
    "HSL": (rgb_to_hsl, hsl_to_rgb),
    "HSV": (rgb_to_hsv, hsv_to_rgb),
    "YIQ": (rgb_to_yiq, yiq_to_rgb),
}

SPACE_CHANNEL_NAMES = {
    "RGB": ("R", "G", "B"),
    "Lab": ("L", "a", "b"),
    "HSL": ("H", "S", "L"),
    "HSV": ("H", "S", "V"),
    "YIQ": ("Y", "I", "Q"),
}