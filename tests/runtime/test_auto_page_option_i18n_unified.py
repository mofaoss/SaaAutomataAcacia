from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication
from qfluentwidgets import ComboBox

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.framework.ui.auto_page.base as auto_page_base
import app.framework.ui.auto_page.i18n_mixin as auto_page_i18n
from app.framework.core.module_system.models import SchemaField
from app.framework.infra.config.app_config import config
from app.framework.ui.auto_page.on_demand import OnDemandAutoPage

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class _DummyConfigItem:
    def __init__(self, value, default, options=None):
        self.value = value
        self.defaultValue = default
        self.options = options
        self.validator = None


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def _make_meta(*fields: SchemaField):
    return SimpleNamespace(id="drink", name="Drink", description="", config_schema=list(fields), actions={})


def _fake_tr_factory(mapping: dict[str, str]):
    def fake_tr(key: str, fallback=None, **_kwargs):
        if key in mapping:
            return mapping[key]
        return fallback if fallback is not None else key

    return fake_tr


def test_explicit_options_prefer_module_option_key_translation(monkeypatch):
    _qapp()
    field = SchemaField(
        param_name="ComboBox_card_mode",
        field_id="ComboBox_card_mode",
        type_hint=int,
        default=0,
        required=False,
        label_key="",
        help_key="",
        label_default="Card Mode",
        help_default="",
        group="General",
        layout="half",
        icon=None,
        description_md=None,
        options=((0, "Fast Mode"), (1, "Safe Mode")),
    )
    item = _DummyConfigItem(value=0, default=0, options=field.options)
    setattr(config, field.param_name, item)
    fake_tr = _fake_tr_factory(
        {
            "module.drink.field.ComboBox_card_mode.option.0": "KEY_FAST",
            "module.drink.field.ComboBox_card_mode.option.1": "KEY_SAFE",
        }
    )
    monkeypatch.setattr(auto_page_base, "tr", fake_tr)
    monkeypatch.setattr(auto_page_i18n, "tr", fake_tr)

    try:
        page = OnDemandAutoPage(module_meta=_make_meta(field))
        widget = page.field_widgets[field.param_name]
        assert isinstance(widget, ComboBox)
        assert widget.itemText(0) == "KEY_FAST"
        assert widget.itemText(1) == "KEY_SAFE"
    finally:
        delattr(config, field.param_name)


def test_explicit_options_fallback_to_literal_label_translation(monkeypatch):
    _qapp()
    field = SchemaField(
        param_name="ComboBox_card_mode",
        field_id="ComboBox_card_mode",
        type_hint=int,
        default=0,
        required=False,
        label_key="",
        help_key="",
        label_default="Card Mode",
        help_default="",
        group="General",
        layout="half",
        icon=None,
        description_md=None,
        options=((0, "Fast Mode"), (1, "Safe Mode")),
    )
    item = _DummyConfigItem(value=0, default=0, options=field.options)
    setattr(config, field.param_name, item)
    fake_tr = _fake_tr_factory({"Fast Mode": "LBL_FAST", "Safe Mode": "LBL_SAFE"})
    monkeypatch.setattr(auto_page_base, "tr", fake_tr)
    monkeypatch.setattr(auto_page_i18n, "tr", fake_tr)

    try:
        page = OnDemandAutoPage(module_meta=_make_meta(field))
        widget = page.field_widgets[field.param_name]
        assert isinstance(widget, ComboBox)
        assert widget.itemText(0) == "LBL_FAST"
        assert widget.itemText(1) == "LBL_SAFE"
    finally:
        delattr(config, field.param_name)
