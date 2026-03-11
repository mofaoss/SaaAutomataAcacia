from __future__ import annotations

import inspect
import re
from enum import Enum
from typing import Any, Literal, get_origin

from app.framework.core.module_system.models import Field, SchemaField
from app.framework.core.module_system.naming import humanize_name


RUNTIME_PARAMS = {
    "self",
    "cls",
    "auto",
    "automation",
    "logger",
    "app_config",
    "config_provider",
    "cancel_token",
    "task_context",
}


def _infer_layout_and_group(param_name: str, type_hint: Any, default_val: Any) -> tuple[str | None, Literal["full", "half"]]:
    """Infers grouping and layout hints using type + naming structure."""
    stripped_name = re.sub(r"^(SpinBox|ComboBox|CheckBox|LineEdit|DoubleSpinBox|Slider|TextEdit)_", "", param_name)
    tokens = [t for t in stripped_name.lower().split("_") if t]
    suffix = tokens[-1] if tokens else ""

    origin = get_origin(type_hint)
    is_prefixed_dropdown = str(param_name).startswith("ComboBox_")
    is_dropdown = is_prefixed_dropdown or origin in (Literal,) or (isinstance(type_hint, type) and issubclass(type_hint, Enum))
    is_numeric = type_hint in (int, float)
    is_bool = type_hint is bool

    compact_tokens = {"upper", "lower", "base", "min", "max", "key", "threshold", "ratio", "times", "count", "mode", "type"}
    long_text_tokens = {"path", "directory", "desc", "description", "content", "json"}

    is_compact_text = any(token in tokens for token in compact_tokens)
    is_long_text = any(token in tokens for token in long_text_tokens)

    if is_bool:
        layout: Literal["full", "half"] = "full"
    elif is_numeric or is_dropdown:
        layout = "half"
    elif is_compact_text and not is_long_text:
        layout = "half"
    else:
        layout = "full"

    calibration_suffixes = {"upper", "lower", "base", "min", "max"}

    group = None
    if suffix in calibration_suffixes:
        group = "Visual Calibration"
    elif len(tokens) >= 2 and suffix == "type":
        # Structural rule: `<domain>_type` naturally forms a dedicated settings section.
        lead = humanize_name(tokens[0])
        group = f"{lead} Settings" if lead else "General"
    elif tokens:
        group = "General"

    return group, layout


def _clean_label(param_name: str) -> str:
    """Removes UI prefixes and humanizes the name."""
    cleaned = re.sub(r"^(SpinBox|ComboBox|CheckBox|LineEdit|DoubleSpinBox|Slider)_", "", param_name)
    return humanize_name(cleaned)


def _resolve_field_meta(
    *,
    module_id: str,
    param_name: str,
    type_hint: Any,
    default_val: Any,
    field_decl: str | Field | None,
) -> tuple[str, str, str | None, str, str, str | None, str, str | None, str | None, tuple[Any, ...] | None]:

    # Default Inference
    inf_group, inf_layout = _infer_layout_and_group(param_name, type_hint, default_val)

    if isinstance(field_decl, Field):
        declared_id = field_decl.id
        declared_label = field_decl.label

        # Backward compatibility: Field("Some Label") should be treated as
        # label-only declaration, not as an unstable field id.
        if (
            declared_label is None
            and isinstance(declared_id, str)
            and declared_id
            and re.fullmatch(r"^[A-Za-z_][A-Za-z0-9_]*$", declared_id) is None
        ):
            declared_label = declared_id
            declared_id = None

        field_id = declared_id or param_name
        # Developer ergonomics: when `label` is omitted, reuse resolved id as
        # the humanized label seed before falling back to param name.
        label_seed = declared_label or field_id or param_name
        label_default = _clean_label(label_seed)
        help_default = field_decl.help
        group = field_decl.group or inf_group
        layout = field_decl.layout
        icon = field_decl.icon
        description_md = field_decl.description_md
        options = tuple(field_decl.options) if field_decl.options is not None else None
    else:
        field_id = param_name
        label_default = field_decl if isinstance(field_decl, str) else _clean_label(param_name)
        help_default = None
        group = inf_group
        layout = inf_layout
        icon = None
        description_md = None
        options = None

    label_key = f"module.{module_id}.field.{field_id}.label"
    help_key = f"module.{module_id}.field.{field_id}.help"
    return field_id, label_default, help_default, label_key, help_key, group, layout, icon, description_md, options


def build_config_schema(
    func,
    *,
    module_id: str,
    fields: dict[str, str | Field] | None = None,
) -> list[SchemaField]:
    sig = inspect.signature(func)
    schema: list[SchemaField] = []
    explicit_fields = fields is not None
    field_defs: dict[str, str | Field] = fields or {}

    for name, param in sig.parameters.items():
        if name in RUNTIME_PARAMS or name.startswith("_") or name.lower() in {"auto", "logger", "islog", "app_config", "automation", "config_provider", "cancel_token", "task_context"}:
            continue
        # If module declares `fields`, treat it as explicit UI schema.
        # Non-declared params remain runtime/internal constructor args.
        if explicit_fields and name not in field_defs:
            continue

        type_hint = param.annotation
        default_val = None if param.default is inspect._empty else param.default

        # Type-driven filtering: skip only when no annotation and no default to infer from.
        # This keeps list/dict/tuple/set fields available for AutoPage typed adapters.
        if default_val is None and type_hint is inspect._empty:
            continue

        if type_hint is inspect._empty and default_val is not None:
            type_hint = type(default_val)

        field_id, label_default, help_default, label_key, help_key, group, layout, icon, description_md, options = _resolve_field_meta(
            module_id=module_id,
            param_name=name,
            type_hint=type_hint,
            default_val=default_val,
            field_decl=field_defs.get(name),
        )

        schema.append(
            SchemaField(
                param_name=name,
                field_id=field_id,
                type_hint=type_hint,
                default=default_val,
                required=param.default is inspect._empty,
                label_key=label_key,
                help_key=help_key,
                label_default=label_default,
                help_default=help_default,
                group=group,
                layout=layout,
                icon=icon,
                description_md=description_md,
                options=options,
            )
        )
    return schema
