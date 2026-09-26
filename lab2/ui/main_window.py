"""

Головне вікно програми.

Розкладка:
    [ Панель керування: кнопки, вибір простору, каналів, інструмент виділення ]
    [ Джерело ]     [ Ціль ]     [ Результат ]    - зліва направо, під панеллю керування

"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QStatusBar,
)

from core.io_bmp import load_bmp, save_bmp, BMPLoadError
from core.colorspaces import CONVERTERS, SPACE_CHANNEL_NAMES
from core.transfer import apply_color_transfer

from .controls_panel import ControlsPanel
from .image_column import ImageColumn


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Статистична корекція кольору")
        self.resize(1300, 850)

        self._source: Optional[np.ndarray] = None
        self._target: Optional[np.ndarray] = None
        self._result: Optional[np.ndarray] = None

        self._space = "Lab"
        self._channels = (True, True, True)
        self._mask: Optional[np.ndarray] = None

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        self.controls = ControlsPanel()
        root_layout.addWidget(self.controls)

        images_layout = QHBoxLayout()
        self.col_source = ImageColumn("Джерело кольору")
        self.col_target = ImageColumn("Ціль (доступне виділення ділянку мишкою)")
        self.col_result = ImageColumn("Результат")
        images_layout.addWidget(self.col_source)
        images_layout.addWidget(self.col_target)
        images_layout.addWidget(self.col_result)
        root_layout.addLayout(images_layout, stretch=1)

        self.setStatusBar(QStatusBar())

        self._connect_signals()
        self.controls.set_channel_labels(SPACE_CHANNEL_NAMES[self._space])



    def _connect_signals(self) -> None:
        c = self.controls
        c.load_source_clicked.connect(lambda: self._load_image("source"))
        c.load_target_clicked.connect(lambda: self._load_image("target"))
        c.save_result_clicked.connect(self._save_result)
        c.apply_clicked.connect(self._run_transfer)
        c.clear_mask_clicked.connect(self._clear_mask)

        c.space_changed.connect(self._on_space_changed)
        c.channels_changed.connect(self._on_channels_changed)
        c.mask_tool_changed.connect(self._on_mask_tool_changed)

        self.col_target.image_panel.mask_changed.connect(self._on_mask_drawn)



    def _load_image(self, which: str) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Оберіть BMP-файл", "", "BMP images (*.bmp)")
        if not path:
            return
        try:
            img = load_bmp(path)
        except BMPLoadError as exc:
            QMessageBox.warning(self, "Помилка завантаження", str(exc))
            return

        if which == "source":
            self._source = img
        else:
            self._target = img
            self._mask = None
            self.col_target.image_panel.clear_mask()

        self._result = None
        self._refresh_all()
        self.statusBar().showMessage(f"Завантажено: {path}", 5000)

    def _save_result(self) -> None:
        if self._result is None:
            QMessageBox.information(self, "Немає результату", "Спочатку застосуйте корекцію кольору.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Зберегти результат", "result.bmp", "BMP images (*.bmp)")
        if not path:
            return
        save_bmp(path, self._result)
        self.statusBar().showMessage(f"Збережено: {path}", 5000)



    def _on_space_changed(self, space: str) -> None:
        self._space = space
        self.controls.set_channel_labels(SPACE_CHANNEL_NAMES[space])
        self._refresh_all()

    def _on_channels_changed(self, channels: tuple) -> None:
        self._channels = channels

    def _on_mask_tool_changed(self, tool) -> None:
        self.col_target.image_panel.set_mask_tool(tool)

    def _on_mask_drawn(self, mask) -> None:
        self._mask = mask

    def _clear_mask(self) -> None:
        self._mask = None
        self.col_target.image_panel.clear_mask()



    def _run_transfer(self) -> None:
        if self._source is None or self._target is None:
            QMessageBox.information(self, "Не вистачає зображень", "Завантажте і джерело, і ціль.")
            return
        try:
            self._result = apply_color_transfer(
                self._source, self._target,
                space=self._space,
                channels=self._channels,
                mask=self._mask,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка корекції", str(exc))
            return
        self._refresh_all()



    def _refresh_all(self) -> None:
        to_space, _ = CONVERTERS[self._space]
        names = SPACE_CHANNEL_NAMES[self._space]

        self.col_source.update_content(
            self._source, to_space(self._source) if self._source is not None else None, names)
        self.col_target.update_content(
            self._target, to_space(self._target) if self._target is not None else None, names)
        self.col_result.update_content(
            self._result, to_space(self._result) if self._result is not None else None, names)