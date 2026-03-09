# coding:utf-8
"""Compatibility shim for periodic task specs."""

from __future__ import annotations

import importlib


def _load_feature_specs():
    module = importlib.import_module("app.features.bootstrap.periodic_task_wiring")
    periodic_specs = getattr(module, "PERIODIC_TASK_SPECS", [])
    primary_task_id = getattr(module, "PRIMARY_PERIODIC_TASK_ID", None)
    return periodic_specs, primary_task_id


PERIODIC_TASK_SPECS, _PRIMARY_TASK_ID = _load_feature_specs()

# Backward-compatible exported name used by legacy callers.
PRIMARY_TASK_ID = _PRIMARY_TASK_ID

__all__ = ["PERIODIC_TASK_SPECS", "PRIMARY_TASK_ID"]
