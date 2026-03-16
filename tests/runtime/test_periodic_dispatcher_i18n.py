from __future__ import annotations

import logging

import pytest

import app.framework.application.periodic.periodic_dispatcher as periodic_dispatcher_module
from app.framework.application.periodic.periodic_dispatcher import PeriodicDispatcher
from app.framework.i18n import _ as _i18n_bootstrap  # noqa: F401
from app.framework.i18n import runtime


class _CaptureLogger:
    def __init__(self) -> None:
        self.messages: list[object] = []

    def info(self, msg, *args, **kwargs):  # noqa: ANN001
        self.messages.append(msg)


@pytest.fixture(autouse=True)
def _isolated_runtime(monkeypatch):
    catalogs = {"en": {}, "zh_CN": {}, "zh_HK": {}}
    monkeypatch.setattr(runtime, "_CATALOGS", catalogs)
    monkeypatch.setattr(runtime, "_LOADED", True)
    monkeypatch.setattr(runtime, "_TELEMETRY_SEEN", set())
    monkeypatch.setattr(runtime, "_SOURCE_TEXT_KEY_BY_OWNER_CONTEXT", {})
    monkeypatch.setattr(runtime, "_SOURCE_TEXT_KEY_GLOBAL", {})
    monkeypatch.setattr(runtime, "_SOURCE_TEXT_INDEX_READY", False)
    monkeypatch.setattr(runtime, "_resolve_lang", lambda: "zh_CN")
    yield


def test_periodic_dispatcher_log_translates_scheduled_trigger_without_msgid(monkeypatch):
    en_key = "framework.ui.scheduled_task_triggered_at_current_time_str_executing_tasks_task_ids"
    runtime._CATALOGS["en"][en_key] = "⏰ Scheduled task triggered at {current_time_str}, executing tasks: {task_ids}"
    runtime._CATALOGS["zh_CN"][en_key] = "⏰ 定时任务在 {current_time_str} 触发，正在执行任务：{task_ids}"

    class _FixedNow:
        def strftime(self, _fmt: str) -> str:
            return "00:58"

    class _FixedDateTime:
        @staticmethod
        def now():
            return _FixedNow()

    monkeypatch.setattr(periodic_dispatcher_module, "datetime", _FixedDateTime)

    logger = _CaptureLogger()
    dispatcher = PeriodicDispatcher(logger)

    queued: list[list[str]] = []
    queued_marks: list[str] = []
    run_now_calls: list[list[str]] = []
    wait_flags: list[bool] = []

    dispatcher.handle_due_tasks(
        ["task_get_reward"],
        is_launch_pending=False,
        is_self_running=False,
        is_external_running=False,
        queue_tasks=lambda tasks: queued.append(list(tasks)),
        mark_task_queued=lambda task_id: queued_marks.append(task_id),
        mark_waiting_for_external_finish=lambda flag: wait_flags.append(flag),
        run_now=lambda tasks: run_now_calls.append(list(tasks)),
    )

    assert queued == []
    assert queued_marks == []
    assert wait_flags == []
    assert run_now_calls == [["task_get_reward"]]
    assert len(logger.messages) == 1

    rendered = runtime.render_message(logger.messages[0], context="log", levelno=logging.INFO)
    assert rendered == "⏰ 定时任务在 00:58 触发，正在执行任务：['task_get_reward']"
