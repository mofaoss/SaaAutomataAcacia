# coding:utf-8
from functools import partial
from typing import Any, Callable

from PySide6.QtWidgets import QPlainTextEdit
from qfluentwidgets import CheckBox, ComboBox, DoubleSpinBox, LineEdit, Slider, SpinBox, SwitchButton

from app.framework.ui.shared.widget_tree import get_all_children


class PeriodicUiBindingUseCase:
    """Encapsulate UI signal wiring for periodic config persistence."""

    @staticmethod
    def connect_config_bindings(
        *,
        root_widget: Any,
        on_widget_change: Callable[[Any], None],
    ) -> None:
        for child in get_all_children(root_widget):
            if isinstance(child, CheckBox):
                child.stateChanged.connect(partial(on_widget_change, child))
            elif isinstance(child, SwitchButton):
                child.checkedChanged.connect(partial(on_widget_change, child))
            elif isinstance(child, ComboBox):
                child.currentIndexChanged.connect(partial(on_widget_change, child))
            elif isinstance(child, LineEdit):
                child.editingFinished.connect(partial(on_widget_change, child))
            elif isinstance(child, SpinBox):
                child.valueChanged.connect(partial(on_widget_change, child))
            elif isinstance(child, DoubleSpinBox):
                child.valueChanged.connect(partial(on_widget_change, child))
            elif isinstance(child, Slider):
                child.valueChanged.connect(partial(on_widget_change, child))
            elif isinstance(child, QPlainTextEdit):
                child.textChanged.connect(partial(on_widget_change, child))
