from __future__ import annotations

import inspect


def _get_section(global_config, section_name: str):
    if global_config is None:
        return None
    return getattr(global_config, section_name, None)


def _try_read_config_value(section, key: str):
    if section is None:
        return None, False
    value_obj = getattr(section, key, None)
    if value_obj is None:
        return None, False
    if hasattr(value_obj, "value"):
        return value_obj.value, True
    return value_obj, True


def build_module_kwargs(meta, global_config, runtime_context: dict):
    sig = inspect.signature(meta.runner)
    kwargs = {}
    section = _get_section(global_config, meta.id)

    for name, param in sig.parameters.items():
        if name in runtime_context:
            kwargs[name] = runtime_context[name]
            continue

        value, ok = _try_read_config_value(section, name)
        if ok:
            kwargs[name] = value
            continue

        if param.default is not inspect._empty:
            kwargs[name] = param.default
            continue

        raise RuntimeError(f"Missing value for parameter '{name}' in module '{meta.id}'")

    return kwargs
