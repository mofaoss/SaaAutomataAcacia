from __future__ import annotations

from typing import Any, Mapping

from app.framework.core.module_system.naming import humanize_name
from app.framework.i18n import tr


def _fallback_title(entity_id: str) -> str:
    normalized = str(entity_id or "").strip()
    if normalized.startswith("task_"):
        normalized = normalized[len("task_") :]
    readable = humanize_name(normalized)
    return readable or str(entity_id or "")


def resolve_display_name(*, name: str, name_msgid: str, fallback_id: str) -> str:
    base_name = str(name or "").strip() or _fallback_title(fallback_id)
    key = str(name_msgid or "").strip()
    if key:
        return tr(key, fallback=base_name)
    return base_name


def resolve_task_display_name(meta: Mapping[str, Any] | None, task_id: str) -> str:
    payload = meta or {}
    return resolve_display_name(
        name=str(payload.get("name", "") or ""),
        name_msgid=str(payload.get("name_msgid", "") or ""),
        fallback_id=task_id,
    )


def resolve_state_display_name(task_name: str, task_name_msgid: str, source: str = "") -> str:
    fallback = str(task_name or "").strip() or str(source or "").strip() or "task"
    return resolve_display_name(
        name=str(task_name or ""),
        name_msgid=str(task_name_msgid or ""),
        fallback_id=fallback,
    )
