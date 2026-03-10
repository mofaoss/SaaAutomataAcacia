from __future__ import annotations

import re


_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
_NON_WORD = re.compile(r"[^a-zA-Z0-9_]+")


def camel_to_snake(name: str) -> str:
    raw = _CAMEL_BOUNDARY.sub("_", name).lower()
    raw = _NON_WORD.sub("_", raw)
    return re.sub(r"_+", "_", raw).strip("_")


def infer_module_id(obj) -> str:
    name = getattr(obj, "__name__", "")
    if not name:
        raise ValueError("Unable to infer module id: target has no __name__")

    if isinstance(obj, type):
        if name.endswith("Module") and len(name) > len("Module"):
            name = name[:-len("Module")]
        return camel_to_snake(name)

    return camel_to_snake(name)


def humanize_name(name: str) -> str:
    return name.replace("_", " ").strip().title()
