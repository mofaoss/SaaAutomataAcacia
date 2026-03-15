# coding:utf-8
"""Periodic task specs generated from module-system metadata."""

from __future__ import annotations

from app.framework.core.module_system import build_periodic_profiles


def _build_periodic_specs():
    profiles = build_periodic_profiles()
    specs = []
    for profile in profiles:
        specs.append(
            {
                "id": profile.get("task_id"),
                "ui_page_index": profile.get("ui_page_index"),
                "option_key": profile.get("option_key"),
                "requires_home_sync": profile.get("requires_home_sync", True),
                "notify_on_completion": profile.get("notify_on_completion", True),
                "enabled_by_default": bool(profile.get("enabled_by_default", False)),
                "is_mandatory": profile.get("mandatory", False),
                "force_first": profile.get("force_first", False),
                "force_last": profile.get("force_last", False),
                "default_activation_config": list(profile.get("default_activation_config", [])),
            }
        )
    return specs


def _pick_primary_task_id(specs):
    for spec in specs:
        if bool(spec.get("force_first", False)):
            return spec.get("id")
    for spec in specs:
        if bool(spec.get("is_mandatory", False)):
            return spec.get("id")
    return specs[0].get("id") if specs else ""


_CACHED_SPECS = None
_CACHED_PRIMARY_ID = None


def get_periodic_task_specs():
    global _CACHED_SPECS
    if _CACHED_SPECS is None:
        _CACHED_SPECS = _build_periodic_specs()
    return _CACHED_SPECS


def get_primary_task_id():
    global _CACHED_PRIMARY_ID
    if _CACHED_PRIMARY_ID is None:
        _CACHED_PRIMARY_ID = _pick_primary_task_id(get_periodic_task_specs())
    return _CACHED_PRIMARY_ID


def clear_task_specs_cache():
    global _CACHED_SPECS, _CACHED_PRIMARY_ID
    _CACHED_SPECS = None
    _CACHED_PRIMARY_ID = None


__all__ = ["get_periodic_task_specs", "get_primary_task_id", "clear_task_specs_cache"]
