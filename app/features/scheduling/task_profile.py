# coding:utf-8
"""Compatibility shim for periodic task profile."""

from app.framework.application.tasks.periodic_task_profile import (  # noqa: F401
    PeriodicTaskProfile,
    get_periodic_task_profile,
)

__all__ = ["PeriodicTaskProfile", "get_periodic_task_profile"]

