from __future__ import annotations

import builtins
import inspect
from pathlib import Path

from app.framework.i18n.runtime import _ as _runtime_translate, tr, TranslatableMessage, get_catalog, load_i18n_catalogs


def _first_external_callsite_frame():
    """Return the first frame outside app.framework.i18n package."""
    frame = inspect.currentframe()
    if frame is None:
        return None
    frame = frame.f_back
    while frame is not None:
        file_name = getattr(getattr(frame, "f_code", None), "co_filename", "")
        normalized = str(file_name).replace("\\", "/").lower()
        if "/app/framework/i18n/" not in normalized:
            return frame
        frame = frame.f_back
    return None


def _is_ui_callsite() -> bool:
    """Detect common UI callsites to auto-materialize TranslatableMessage -> str."""
    try:
        caller = _first_external_callsite_frame()
        file_path = Path(getattr(getattr(caller, "f_code", None), "co_filename", ""))
        parts = [p.lower() for p in file_path.parts]
        if "ui" in parts:
            return True
        if "views" in parts and "framework" in parts:
            return True
    except Exception:
        return False
    return False


def _infer_owner_hints_from_callsite() -> dict:
    """Best-effort owner/callsite inference when AST rewrite metadata is unavailable."""
    hints: dict = {}
    try:
        caller = _first_external_callsite_frame()
        code = getattr(caller, "f_code", None)
        file_name = Path(getattr(code, "co_filename", ""))
        parts = [p.lower() for p in file_name.parts]

        owner_scope = "framework"
        owner_module = None
        try:
            mod_idx = parts.index("modules")
            owner_scope = "module"
            owner_module = file_name.parts[mod_idx + 1]
        except Exception:
            if "framework" in parts:
                owner_scope = "framework"
            else:
                owner_scope = "framework"

        normalized_path = str(file_name).replace("\\", "/")
        callsite_key = (
            f"{normalized_path}:{getattr(caller, 'f_lineno', 0)}:0"
            if caller is not None
            else None
        )

        context_hint = "ui" if _is_ui_callsite() else "log"

        hints["__i18n_owner_scope__"] = owner_scope
        hints["__i18n_owner_module__"] = owner_module
        if callsite_key:
            hints["__i18n_callsite_key__"] = callsite_key
        hints["__i18n_context_hint__"] = context_hint
    except Exception:
        return {}
    return hints


def _builtin_translate(text, *, msgid=None, **kwargs):
    """Builtin `_` bridge: keep authoring API native while avoiding Qt type crashes."""
    # If import rewrite metadata is missing, recover owner/callsite so keys still land
    # in module catalogs instead of incorrectly falling back to framework.*.
    if "__i18n_owner_scope__" not in kwargs:
        kwargs.update(_infer_owner_hints_from_callsite())
    value = _runtime_translate(text, msgid=msgid, **kwargs)
    if _is_ui_callsite():
        return str(value) if value is not None else ""
    return value


def _(text, *, msgid=None, **kwargs):
    """Public `_` export with automatic Qt-safe adaptation on UI callsites."""
    return _builtin_translate(text, msgid=msgid, **kwargs)


def install_global_translate_symbol() -> None:
    """Expose `_` as a global builtin so modules can use native `_()` authoring."""
    try:
        setattr(builtins, "_", _builtin_translate)
    except Exception:
        # Never block startup if builtin injection fails in restricted runtimes.
        pass


install_global_translate_symbol()

__all__ = ["_", "tr", "TranslatableMessage", "load_i18n_catalogs", "get_catalog"]
