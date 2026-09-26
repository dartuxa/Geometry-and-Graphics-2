"""

Віджет для показу одного зображення.

Для зображення-цілі (target) підтримує малювання маски мишкою
(прямокутник або круг) - використовується для локальної корекції кольору.

"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PyQt5.QtCore import Qt, QEvent, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy

from core.mask import rectangle_mask, circle_mask
from .utils import numpy_rgb_to_pixmap


class ImagePanel(QWidget):
    """Показує зображення та (опційно) дозволяє малювати маску-виділення мишкою."""

    mask_changed = pyqtSignal(object) # np.ndarray | None

    MAX_DISPLAY_SIZE = 360

    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._image: Optional[np.ndarray] = None # (H, W, 3) float [0,1]
        self._display_scale: float = 1.0
        self._displayed_size: tuple[int, int] = (0, 0) # розмір (w, h) намальованого pixmap у мітці
        self._mask_tool: Optional[str] = None # None | "rect" | "circle"
        self._drag_start: Optional[QPoint] = None
        self._drag_current: Optional[QPoint] = None
        self._mask: Optional[np.ndarray] = None

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 13px;")

        self.image_label = QLabel("Зображення не завантажено")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(220, 160)
        self.image_label.setStyleSheet(
            "border: 1px solid #888; background: #202020; color: #999;"
        )
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.installEventFilter(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label)
    
    
    
    def set_image(self, img: Optional[np.ndarray]) -> None:
        """Встановлює нове зображення (H, W, 3) float [0,1], або None."""
        self._image = img
        self._mask = None
        self._drag_start = None
        self._drag_current = None
        self._refresh_pixmap()

    def image(self) -> Optional[np.ndarray]:
        return self._image

    def set_mask_tool(self, tool: Optional[str]) -> None:
        """tool: None (виключено), 'rect' або 'circle'."""
        self._mask_tool = tool

    def current_mask(self) -> Optional[np.ndarray]:
        return self._mask

    def clear_mask(self) -> None:
        self._mask = None
        self.mask_changed.emit(None)
        self._refresh_pixmap()



    def _refresh_pixmap(self) -> None:
        if self._image is None:
            self.image_label.setText("Зображення не завантажено")
            self.image_label.setPixmap(QPixmap())
            return

        pixmap = numpy_rgb_to_pixmap(self._image)
        scaled = pixmap.scaled(
            self.MAX_DISPLAY_SIZE, self.MAX_DISPLAY_SIZE,
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        self._display_scale = scaled.width() / pixmap.width() if pixmap.width() else 1.0
        self._displayed_size = (scaled.width(), scaled.height())

        if self._mask_tool is not None and self._drag_start and self._drag_current:
            scaled = self._draw_preview(scaled)

        self.image_label.setPixmap(scaled)

    def _draw_preview(self, pixmap: QPixmap) -> QPixmap:
        """Малює контур поточного виділення поверх зменшеної картинки під час перетягування."""
        pm = QPixmap(pixmap)
        painter = QPainter(pm)
        pen = QPen(QColor(255, 215, 0), 2, Qt.DashLine)
        painter.setPen(pen)
        p0, p1 = self._drag_start, self._drag_current
        if self._mask_tool == "rect":
            painter.drawRect(
                min(p0.x(), p1.x()), min(p0.y(), p1.y()),
                abs(p1.x() - p0.x()), abs(p1.y() - p0.y()),
            )
        elif self._mask_tool == "circle":
            r = int(((p1.x() - p0.x()) ** 2 + (p1.y() - p0.y()) ** 2) ** 0.5)
            painter.drawEllipse(p0, r, r)
        painter.end()
        return pm



    def _label_pos_to_pixmap_pos(self, pos: QPoint) -> QPoint:
        """
        QLabel зазвичай більший за саму картинку (через Expanding-політику
        розміру та stretch у компонуванні), а картинка малюється по центру
        мітки (AlignCenter). Тому позицію курсора в координатах мітки треба
        зсунути на відступ між рамкою мітки та фактично намальованим pixmap,
        інакше виділення "з'їжджає" відносно курсора.
        """
        disp_w, disp_h = self._displayed_size
        offset_x = (self.image_label.width() - disp_w) / 2
        offset_y = (self.image_label.height() - disp_h) / 2

        x = pos.x() - offset_x
        y = pos.y() - offset_y
        
        x = min(max(x, 0), max(disp_w - 1, 0))
        y = min(max(y, 0), max(disp_h - 1, 0))
        return QPoint(int(x), int(y))

    def eventFilter(self, obj, event):
        if obj is self.image_label and self._mask_tool is not None and self._image is not None:
            et = event.type()
            if et == QEvent.MouseButtonPress:
                pos = self._label_pos_to_pixmap_pos(event.pos())
                self._drag_start = pos
                self._drag_current = pos
                return True
            if et == QEvent.MouseMove and self._drag_start is not None:
                self._drag_current = self._label_pos_to_pixmap_pos(event.pos())
                self._refresh_pixmap()
                return True
            if et == QEvent.MouseButtonRelease and self._drag_start is not None:
                self._drag_current = self._label_pos_to_pixmap_pos(event.pos())
                self._finish_mask_drag()
                return True
        return super().eventFilter(obj, event)

    def _finish_mask_drag(self) -> None:
        p0, p1 = self._drag_start, self._drag_current
        self._drag_start = None
        self._drag_current = None

        if self._image is None or p0 is None or p1 is None or self._display_scale == 0:
            return

        h, w = self._image.shape[:2]
        x0, y0 = p0.x() / self._display_scale, p0.y() / self._display_scale
        x1, y1 = p1.x() / self._display_scale, p1.y() / self._display_scale

        if self._mask_tool == "rect":
            mask = rectangle_mask((h, w), x0, y0, x1, y1)
        elif self._mask_tool == "circle":
            radius = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            mask = circle_mask((h, w), x0, y0, radius)
        else:
            return

        self._mask = mask
        self.mask_changed.emit(mask)
        self._refresh_pixmap()