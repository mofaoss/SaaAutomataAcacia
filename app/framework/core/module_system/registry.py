from __future__ import annotations

import threading
from typing import Any

from app.framework.core.module_system.models import ModuleHost, ModuleMeta


_MODULE_REGISTRY: dict[str, ModuleMeta] = {}
_BOOTSTRAP_LOCK = threading.Lock()
_BOOTSTRAPPED = False


def _ensure_discovered():
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    with _BOOTSTRAP_LOCK:
        if _BOOTSTRAPPED:
            return
        from app.framework.core.module_system.discovery import discover_modules

        discover_modules("app.features.modules")
        _BOOTSTRAPPED = True


def register_module(meta: ModuleMeta):
    _MODULE_REGISTRY[meta.id] = meta


def get_module(module_id: str) -> ModuleMeta | None:
    return _MODULE_REGISTRY.get(module_id)


def get_all_modules() -> list[ModuleMeta]:
    _ensure_discovered()
    return list(_MODULE_REGISTRY.values())


def get_modules_by_host(host: ModuleHost) -> list[ModuleMeta]:
    _ensure_discovered()
    return sorted(
        [m for m in _MODULE_REGISTRY.values() if m.host == host and m.enabled],
        key=lambda x: x.order,
    )


def _first_default_activation_config(meta: ModuleMeta) -> list[dict[str, Any]]:
    if meta.periodic_default_activation_config:
        return list(meta.periodic_default_activation_config)
    return [
        {
            "type": "daily",
            "day": 0,
            "time": f"{int(meta.periodic_default_hour):02d}:{int(meta.periodic_default_minute):02d}",
            "max_runs": int(meta.periodic_max_runs),
        }
    ]


def build_periodic_profiles():
    profiles = []
    for m in get_modules_by_host(ModuleHost.PERIODIC):
        profiles.append(
            {
                "task_id": m.id,
                "title": m.name,
                "enabled_by_default": m.periodic_enabled_by_default,
                "mandatory": m.periodic_mandatory,
                "force_first": m.periodic_force_first,
                "default_hour": m.periodic_default_hour,
                "default_minute": m.periodic_default_minute,
                "max_runs": m.periodic_max_runs,
                "ui_page_index": m.periodic_ui_page_index,
                "option_key": m.periodic_option_key,
                "requires_home_sync": m.periodic_requires_home_sync,
                "default_activation_config": _first_default_activation_config(m),
            }
        )
    return profiles


def clear_registry():
    _MODULE_REGISTRY.clear()
    global _BOOTSTRAPPED
    _BOOTSTRAPPED = False
