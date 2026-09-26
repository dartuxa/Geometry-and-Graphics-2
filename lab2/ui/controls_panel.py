"""

Панель керування: завантаження зображень, вибір колірного простору,
вибір каналів для корекції, вибір інструмента виділення ділянки,
застосування корекції та збереження результату.

"""
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QCheckBox,
    QButtonGroup, QRadioButton, QGroupBox,
)

from core.colorspaces import CONVERTERS


class ControlsPanel(QWidget):
    """Імітує сигнали, нічого не знає про core/UI-стан - цим керує MainWindow."""

    load_source_clicked = pyqtSignal()
    load_target_clicked = pyqtSignal()
    save_result_clicked = pyqtSignal()
    apply_clicked = pyqtSignal()
    clear_mask_clicked = pyqtSignal()

    space_changed = pyqtSignal(str) # "Lab" / "HSL" / "HSV" / "YIQ"
    channels_changed = pyqtSignal(tuple) # (bool, bool, bool)
    mask_tool_changed = pyqtSignal(object) # None / "rect" / "circle"

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)

        self.btn_load_source = QPushButton("Завантажити джерело")
        self.btn_load_target = QPushButton("Завантажити ціль")
        self.btn_load_source.clicked.connect(self.load_source_clicked)
        self.btn_load_target.clicked.connect(self.load_target_clicked)
        layout.addWidget(self.btn_load_source)
        layout.addWidget(self.btn_load_target)

        space_box = QGroupBox("Простір")
        space_layout = QVBoxLayout(space_box)
        self.combo_space = QComboBox()
        self.combo_space.addItems(list(CONVERTERS.keys()))
        self.combo_space.currentTextChanged.connect(self.space_changed)
        space_layout.addWidget(self.combo_space)
        layout.addWidget(space_box)

        channels_box = QGroupBox("Канали корекції")
        channels_layout = QHBoxLayout(channels_box)
        self.chk_c0 = QCheckBox("1")
        self.chk_c1 = QCheckBox("2")
        self.chk_c2 = QCheckBox("3")
        for chk in (self.chk_c0, self.chk_c1, self.chk_c2):
            chk.setChecked(True)
            chk.stateChanged.connect(self._emit_channels_changed)
            channels_layout.addWidget(chk)
        layout.addWidget(channels_box)

        mask_box = QGroupBox("Ділянка корекції")
        mask_layout = QHBoxLayout(mask_box)
        self.radio_none = QRadioButton("Все зображення")
        self.radio_rect = QRadioButton("Прямокутник")
        self.radio_circle = QRadioButton("Коло")
        self.radio_none.setChecked(True)
        self.mask_group = QButtonGroup(self)
        for idx, rb in enumerate((self.radio_none, self.radio_rect, self.radio_circle)):
            self.mask_group.addButton(rb, idx)
            mask_layout.addWidget(rb)
        self.mask_group.idClicked.connect(self._emit_mask_tool_changed)

        self.btn_clear_mask = QPushButton("Скинути ділянку")
        self.btn_clear_mask.clicked.connect(self.clear_mask_clicked)
        mask_layout.addWidget(self.btn_clear_mask)
        layout.addWidget(mask_box)

        layout.addStretch(1)

        self.btn_apply = QPushButton("Застосувати корекцію")
        self.btn_apply.setStyleSheet("font-weight: bold;")
        self.btn_save = QPushButton("Зберегти результат")
        self.btn_apply.clicked.connect(self.apply_clicked)
        self.btn_save.clicked.connect(self.save_result_clicked)
        layout.addWidget(self.btn_apply)
        layout.addWidget(self.btn_save)

    def _emit_channels_changed(self) -> None:
        self.channels_changed.emit((
            self.chk_c0.isChecked(),
            self.chk_c1.isChecked(),
            self.chk_c2.isChecked(),
        ))

    def _emit_mask_tool_changed(self, idx: int) -> None:
        tool = {0: None, 1: "rect", 2: "circle"}[idx]
        self.mask_tool_changed.emit(tool)

    def set_channel_labels(self, names: tuple[str, str, str]) -> None:
        """Підписує чекбокси каналів назвами поточного простору (L/a/b, H/S/L тощо)."""
        self.chk_c0.setText(names[0])
        self.chk_c1.setText(names[1])
        self.chk_c2.setText(names[2])