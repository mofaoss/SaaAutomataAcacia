# coding:utf-8
import copy
import json
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPlainTextEdit, QTreeWidget
from qfluentwidgets import CheckBox, ComboBox, DoubleSpinBox, LineEdit, Slider, SpinBox, SwitchButton

from app.framework.infra.config.app_config import config


class PeriodicSettingsUseCase:
    """Typed boundary for periodic settings read/write and preset persistence."""

    @staticmethod
    def should_check_update_on_startup() -> bool:
        return bool(config.checkUpdateAtStartUp.value)

    @staticmethod
    def is_auto_open_game_enabled() -> bool:
        return bool(config.CheckBox_open_game_directly.value)

    @staticmethod
    def is_same_game_directory(folder: str) -> bool:
        return str(config.LineEdit_game_directory.value) == str(folder)

    @staticmethod
    def _value_matches(left: Any, right: Any) -> bool:
        if left == right:
            return True
        try:
            return str(left) == str(right)
        except Exception:
            return False

    @staticmethod
    def _combo_set_value(widget: ComboBox, value: Any) -> None:
        values = widget.property("_auto_option_values")
        if isinstance(values, list) and values:
            for idx, option in enumerate(values):
                if PeriodicSettingsUseCase._value_matches(option, value):
                    widget.setCurrentIndex(idx)
                    return

            labels = widget.property("_auto_option_labels")
            if isinstance(labels, list):
                for idx, label in enumerate(labels):
                    if PeriodicSettingsUseCase._value_matches(label, value):
                        widget.setCurrentIndex(idx)
                        return

            # Backward compatibility: legacy configs may store combo index.
            if isinstance(value, int) and 0 <= value < len(values):
                widget.setCurrentIndex(value)
                return

        text = str(value)
        index = widget.findText(text)
        if index >= 0:
            widget.setCurrentIndex(index)
            return

        try:
            widget.setCurrentIndex(int(value))
        except Exception:
            pass

    @staticmethod
    def _combo_get_value(widget: ComboBox) -> Any:
        index = int(widget.currentIndex())
        values = widget.property("_auto_option_values")
        if isinstance(values, list) and 0 <= index < len(values):
            return values[index]
        return index

    @staticmethod
    def _stringify_for_text_widget(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (list, tuple, set, dict)):
            normalized = list(value) if isinstance(value, set) else value
            try:
                return json.dumps(normalized, ensure_ascii=False, indent=2)
            except Exception:
                return str(value)
        return str(value)

    @staticmethod
    def _coerce_text_for_config(text: str, sample: Any) -> Any:
        raw = str(text or "")
        stripped = raw.strip()

        if isinstance(sample, bool):
            return stripped.lower() in {"1", "true", "yes", "on"}

        if isinstance(sample, int) and not isinstance(sample, bool):
            try:
                return int(float(stripped))
            except Exception:
                return sample

        if isinstance(sample, float):
            try:
                return float(stripped)
            except Exception:
                return sample

        if isinstance(sample, dict):
            if not stripped:
                return {}
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            return sample

        if isinstance(sample, list):
            if not stripped:
                return []
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
            return [part.strip() for part in re.split(r"[\n,]", stripped) if part.strip()]

        if isinstance(sample, tuple):
            parsed = PeriodicSettingsUseCase._coerce_text_for_config(stripped, list(sample))
            return tuple(parsed) if isinstance(parsed, list) else sample

        if isinstance(sample, set):
            parsed = PeriodicSettingsUseCase._coerce_text_for_config(stripped, list(sample))
            return set(parsed) if isinstance(parsed, list) else sample

        return raw

    @staticmethod
    def apply_config_to_widgets(widgets: Iterable[Any]) -> None:
        for widget in widgets:
            config_item = getattr(config, widget.objectName(), None)
            if config_item is None:
                continue

            if isinstance(widget, CheckBox):
                widget.setChecked(bool(config_item.value))
            elif isinstance(widget, SwitchButton):
                widget.setChecked(bool(config_item.value))
            elif isinstance(widget, ComboBox):
                PeriodicSettingsUseCase._combo_set_value(widget, config_item.value)
            elif isinstance(widget, LineEdit):
                widget.setText(str(config_item.value))
            elif isinstance(widget, SpinBox):
                try:
                    widget.setValue(int(config_item.value))
                except Exception:
                    widget.setValue(0)
            elif isinstance(widget, DoubleSpinBox):
                try:
                    widget.setValue(float(config_item.value))
                except Exception:
                    widget.setValue(0.0)
            elif isinstance(widget, Slider):
                try:
                    widget.setValue(int(config_item.value))
                except Exception:
                    pass
            elif isinstance(widget, QPlainTextEdit):
                widget.setPlainText(PeriodicSettingsUseCase._stringify_for_text_widget(config_item.value))

    @staticmethod
    def apply_tree_selection(tree: QTreeWidget, text_to_key: Dict[str, str]) -> None:
        from PySide6.QtWidgets import QTreeWidgetItemIterator

        item = QTreeWidgetItemIterator(tree)
        while item.value():
            text = item.value().text(0)
            item_key = text_to_key.get(text)
            config_item = getattr(config, item_key, None) if item_key else None
            if config_item is not None:
                item.value().setCheckState(
                    0,
                    Qt.CheckState.Checked if bool(config_item.value) else Qt.CheckState.Unchecked,
                )
            item += 1

    @staticmethod
    def persist_widget_change(widget: Any) -> Optional[bool]:
        config_item = getattr(config, widget.objectName(), None)
        if config_item is None:
            return None

        if isinstance(widget, CheckBox):
            checked = bool(widget.isChecked())
            config.set(config_item, checked)
            if widget.objectName() == "CheckBox_is_use_power":
                return checked
            return None

        if isinstance(widget, SwitchButton):
            checked = bool(widget.isChecked())
            config.set(config_item, checked)
            if widget.objectName() == "CheckBox_is_use_power":
                return checked
            return None

        if isinstance(widget, ComboBox):
            config.set(config_item, PeriodicSettingsUseCase._combo_get_value(widget))
            return None

        if isinstance(widget, SpinBox):
            config.set(config_item, int(widget.value()))
            return None

        if isinstance(widget, DoubleSpinBox):
            config.set(config_item, float(widget.value()))
            return None

        if isinstance(widget, Slider):
            config.set(config_item, int(widget.value()))
            return None

        if isinstance(widget, QPlainTextEdit):
            sample = getattr(config_item, "value", None)
            if sample is None:
                sample = getattr(config_item, "defaultValue", None)
            parsed = PeriodicSettingsUseCase._coerce_text_for_config(widget.toPlainText(), sample)
            config.set(config_item, parsed)
            return None

        if isinstance(widget, LineEdit):
            name = widget.objectName()
            text = widget.text()
            if any(token in name for token in ("x1", "x2", "y1", "y2")):
                try:
                    config.set(config_item, int(text))
                except ValueError:
                    return None
            else:
                config.set(config_item, text)
            return None

        return None

    @staticmethod
    def persist_indexed_item(prefix: str, index: int, check_state: int) -> None:
        config_item = getattr(config, f"{prefix}{index}", None)
        if config_item is not None:
            config.set(config_item, check_state != 0)

    @staticmethod
    def reset_redeem_codes() -> str:
        content = ""
        if config.import_codes.value:
            config.set(config.import_codes, [])
            content += " 导入 "
        if config.used_codes.value:
            config.set(config.used_codes, [])
            content += " 已使用 "
        return content

    @staticmethod
    def parse_import_codes(raw_text: str) -> List[str]:
        lines = (raw_text or "").splitlines()
        result = []
        for line in lines:
            stripped_line = line.strip()
            if ":" in stripped_line:
                result.append(stripped_line.split(":")[-1])
            elif "：" in stripped_line:
                result.append(stripped_line.split("：")[-1])
            else:
                result.append(stripped_line)
        return result

    @staticmethod
    def save_import_codes(codes: List[str]) -> None:
        config.set(config.import_codes, list(codes))

    @staticmethod
    def save_date_tip(tips: Dict[str, Any]) -> None:
        config.set(config.date_tip, tips)

    @staticmethod
    def load_date_tip() -> Optional[Dict[str, Any]]:
        if not config.date_tip.value:
            return None
        return copy.deepcopy(config.date_tip.value)

    @staticmethod
    def is_log_enabled() -> bool:
        return bool(config.isLog.value)

    @staticmethod
    def load_presets() -> Dict[str, Any]:
        presets = config.task_presets.value
        if not presets:
            presets = {"Default": {"task_ids": [], "task_configs": {}}}
            config.set(config.task_presets, presets)
        return dict(presets)

    @staticmethod
    def get_preset_data(preset_name: str) -> Dict[str, Any]:
        presets = PeriodicSettingsUseCase.load_presets()
        data = presets.get(preset_name, {})
        if isinstance(data, list):
            # Compatibility with legacy list-only presets
            return {"task_ids": data, "task_configs": {}}
        return data

    @staticmethod
    def save_preset(preset_name: str, enabled_tasks: List[str], task_configs: Dict[str, Any]) -> None:
        presets = PeriodicSettingsUseCase.load_presets()
        presets[preset_name] = {
            "task_ids": list(enabled_tasks),
            "task_configs": copy.deepcopy(task_configs)
        }
        config.set(config.task_presets, presets)

    @staticmethod
    def delete_preset(preset_name: str) -> Tuple[bool, str]:
        presets = PeriodicSettingsUseCase.load_presets()
        if preset_name not in presets:
            return False, "not_found"
        if len(presets) <= 1:
            return False, "min_one_required"
        del presets[preset_name]
        config.set(config.task_presets, presets)
        
        # If deleted preset was the last used, reset to first available
        if config.last_preset.value == preset_name:
            config.set(config.last_preset, list(presets.keys())[0])
            
        return True, "deleted"

    @staticmethod
    def rename_preset(old_name: str, new_name: str) -> bool:
        if not new_name or old_name == new_name:
            return False
        presets = PeriodicSettingsUseCase.load_presets()
        if old_name not in presets:
            return False
        
        # If new name already exists, we don't allow overwrite via rename
        if new_name in presets:
            return False
            
        presets[new_name] = presets.pop(old_name)
        config.set(config.task_presets, presets)
        
        if config.last_preset.value == old_name:
            config.set(config.last_preset, new_name)
        return True

    @staticmethod
    def save_last_preset(preset_name: str) -> None:
        config.set(config.last_preset, preset_name)

    @staticmethod
    def load_last_preset() -> str:
        name = config.last_preset.value
        presets = PeriodicSettingsUseCase.load_presets()
        if name not in presets:
            return list(presets.keys())[0]
        return name

    @staticmethod
    def generate_next_default_name() -> str:
        counter = config.preset_counter.value + 1
        config.set(config.preset_counter, counter)
        return f"default_{counter}"

    @staticmethod
    def get_all_task_configs() -> Dict[str, Any]:
        """Snapshot all task-related ConfigItems from the current global config."""
        res = {}
        # Only include groups that are task-specific and safe to snapshot/serialize
        include_groups = {
            "home_interface_enter", "home_interface_option", "home_interface_close",
            "home_interface_person", "home_interface_power", "home_interface_reward",
            "home_interface_shopping", "home_interface_shopping_person", "home_interface_shopping_weapon",
            "ShardExchange", "automation", "add_action", "add_fish", "add_trigger",
            "add_alien", "add_maze", "add_massaging", "add_drink", "add_water",
            "jigsaw", "pieces_num", "add_capture_pals", "DailyTasks"
        }
        
        from qfluentwidgets import ConfigItem
        for attr in dir(config):
            item = getattr(config, attr, None)
            if isinstance(item, ConfigItem):
                # Skip metadata and internal state
                if attr in {"task_presets", "last_preset", "preset_counter"}:
                    continue
                
                # Only include task-related groups
                if not hasattr(item, "group") or item.group not in include_groups:
                    continue

                val = item.value
                try:
                    # We try to deepcopy to detach from current state
                    res[attr] = copy.deepcopy(val)
                except Exception:
                    res[attr] = val
        return res

    @staticmethod
    def apply_config_snapshot(snapshot: Dict[str, Any]) -> None:
        """Apply a previously saved snapshot back to the global config."""
        if not snapshot:
            return
        from qfluentwidgets import ConfigItem
        for attr, value in snapshot.items():
            item = getattr(config, attr, None)
            if isinstance(item, ConfigItem):
                try:
                    config.set(item, value)
                except Exception:
                    # If setting fails (e.g. validator mismatch in old preset), skip it
                    pass
