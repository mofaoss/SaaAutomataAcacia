# coding:utf-8
"""Periodic default sequence generated from module-system metadata."""

from __future__ import annotations

import copy

from app.framework.application.tasks.periodic_task_specs import get_periodic_task_specs


def build_default_periodic_task_sequence():
    sequence = []
    for spec in get_periodic_task_specs():
        task_id = spec.get("id")
        if not task_id:
            continue
            
        default_rules = spec.get("default_activation_config") or [
            {
                "type": "daily",
                "day": 0,
                "time": "00:00",
                "max_runs": 1,
            }
        ]
        sequence.append(
            {
                "id": task_id,
                "enabled": False,
                "use_periodic": bool(spec.get("enabled_by_default", False)),
                "last_run": 0,
                "activation_config": copy.deepcopy(default_rules),
                "execution_config": [],
                "force_last": bool(spec.get("force_last", False)),
            }
        )
    return sequence


__all__ = ["build_default_periodic_task_sequence"]
