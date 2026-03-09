# coding:utf-8
"""Compatibility shim for periodic default task sequence."""

from __future__ import annotations

import importlib


def build_default_periodic_task_sequence():
    module = importlib.import_module("app.features.bootstrap.periodic_task_wiring")
    builder = getattr(module, "build_default_periodic_task_sequence", None)
    if callable(builder):
        return builder()
    return []


__all__ = ["build_default_periodic_task_sequence"]
