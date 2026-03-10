# coding:utf-8
"""Periodic default sequence generated from module-system metadata."""

from __future__ import annotations

import copy

from app.framework.core.module_system import build_periodic_profiles


def build_default_periodic_task_sequence():
    sequence = []
    for profile in build_periodic_profiles():
        default_rules = profile.get("default_activation_config") or [
            {
                "type": "daily",
                "day": 0,
                "time": f"{int(profile.get('default_hour', 4)):02d}:{int(profile.get('default_minute', 0)):02d}",
                "max_runs": int(profile.get("max_runs", 1)),
            }
        ]
        sequence.append(
            {
                "id": profile.get("task_id"),
                "enabled": False,
                "use_periodic": bool(profile.get("enabled_by_default", False)),
                "last_run": 0,
                "activation_config": copy.deepcopy(default_rules),
                "execution_config": [],
            }
        )
    return sequence


__all__ = ["build_default_periodic_task_sequence"]
