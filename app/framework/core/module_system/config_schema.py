from __future__ import annotations

import inspect


RUNTIME_PARAMS = {
    "self",
    "cls",
    "auto",
    "automation",
    "logger",
    "cancel_token",
    "task_context",
}


def build_config_schema(func):
    sig = inspect.signature(func)
    schema = []
    for name, param in sig.parameters.items():
        if name in RUNTIME_PARAMS:
            continue
        schema.append(
            {
                "name": name,
                "type": param.annotation,
                "default": None if param.default is inspect._empty else param.default,
                "required": param.default is inspect._empty,
            }
        )
    return schema
