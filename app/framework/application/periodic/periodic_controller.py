# coding:utf-8
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.framework.application.periodic.periodic_orchestration import normalize_tasks_for_launch
from app.framework.core.task_engine.threads import TaskQueueThread


@dataclass
class RunPlan:
    final_tasks: List[str]
    should_launch_game: bool
    should_warn_game_not_open: bool


@dataclass
class ThreadTransition:
    flag: str
    started: bool = False
    stopped: bool = False
    should_after_finish: bool = False


@dataclass
class PeriodicControllerState:
    is_running: bool = False
    is_launch_pending: bool = False
    is_global_running: bool = False
    waiting_for_external_to_finish: bool = False
    tasks_to_run: List[str] = field(default_factory=list)
    launch_process: Any = None
    launch_deadline: float = 0.0
    is_running_solo: bool = False
    is_scheduled_run: bool = False


class PeriodicController:
    """Application layer controller for periodic execution state and thread lifecycle."""

    def __init__(self, task_registry: Dict[str, dict], primary_task_id: str):
        self.task_registry = task_registry
        self.primary_task_id = primary_task_id
        self.state = PeriodicControllerState()
        self._start_thread: Optional[TaskQueueThread] = None

    @property
    def start_thread(self) -> Optional[TaskQueueThread]:
        return self._start_thread

    @start_thread.setter
    def start_thread(self, thread: Optional[TaskQueueThread]):
        self._start_thread = thread

    def set_global_running(self, is_running: bool):
        self.state.is_global_running = bool(is_running)

    def _ensure_cleanup_at_end(self, task_ids: List[str]) -> List[str]:
        """通用逻辑：确保带有置底属性的任务始终处于序列末尾"""
        if not task_ids:
            return []
        
        # 提取出所有普通任务和所有置底任务
        normal_tasks = []
        cleanup_tasks = []
        
        for tid in task_ids:
            meta = self.task_registry.get(tid, {})
            if meta.get("force_last") or meta.get("periodic_role") == "cleanup":
                cleanup_tasks.append(tid)
            else:
                normal_tasks.append(tid)
        
        # 重新组合：普通在前，置底在后（保持内部相对顺序）
        return normal_tasks + cleanup_tasks

    def queue_tasks(self, task_ids: List[str]):
        """入队逻辑：合并并重新应用排序规则"""
        combined = self.state.tasks_to_run + task_ids
        self.state.tasks_to_run = self._ensure_cleanup_at_end(combined)

    def mark_waiting_for_external_finish(self, waiting: bool):
        self.state.waiting_for_external_to_finish = bool(waiting)

    def consume_pending_queue_on_external_release(self) -> List[str]:
        if (
            self.state.waiting_for_external_to_finish
            and self.state.tasks_to_run
            and not self.state.is_running
            and not self.state.is_launch_pending
        ):
            self.state.waiting_for_external_to_finish = False
            return list(self.state.tasks_to_run)
        return []

    def build_run_plan(
        self,
        task_ids: List[str],
        *,
        game_opened: bool,
        auto_open_game_enabled: bool,
        cleanup_enabled: bool = False,
    ) -> RunPlan:
        should_launch_game = (not game_opened) and bool(auto_open_game_enabled)
        
        # 1. 基础序列标准化 (处理 bootstrap 等)
        final_tasks = list(normalize_tasks_for_launch(
            task_ids=task_ids,
            primary_task_id=self.primary_task_id,
            should_force_primary=should_launch_game or self.primary_task_id in task_ids,
        ))

        # 2. 通用 Cleanup 注入与排序 (根据角色声明)
        if cleanup_enabled:
            # 找出所有声明了 cleanup 角色但不在列表中的任务并追加
            for tid, meta in self.task_registry.items():
                if (meta.get("force_last") or meta.get("periodic_role") == "cleanup") and tid not in final_tasks:
                    final_tasks.append(tid)
        
        # 3. 强制二次校验：确保无论何种注入方式，置底任务都在最后
        final_tasks = self._ensure_cleanup_at_end(final_tasks)

        self.state.tasks_to_run = list(final_tasks)
        return RunPlan(
            final_tasks=list(final_tasks),
            should_launch_game=should_launch_game,
            should_warn_game_not_open=(not game_opened) and (not should_launch_game),
        )

    def update_launch_pending(self, pending: bool):
        self.state.is_launch_pending = bool(pending)

    def mark_launch_started(self, process: Any, timeout_seconds: float = 90.0):
        self.state.launch_process = process
        self.state.launch_deadline = time.time() + timeout_seconds
        self.state.is_launch_pending = True

    def clear_launch_watch_state(self):
        self.state.launch_deadline = 0.0
        self.state.launch_process = None

    def check_launch_tick(self, *, game_window_open: bool, now: Optional[float] = None) -> str:
        if game_window_open:
            self.clear_launch_watch_state()
            self.state.is_launch_pending = False
            return "detected"

        launch_process = self.state.launch_process
        if launch_process is not None and launch_process.poll() is not None:
            self.clear_launch_watch_state()
            self.state.is_launch_pending = False
            return "process_exited"

        current_time = time.time() if now is None else now
        if self.state.launch_deadline and current_time > self.state.launch_deadline:
            self.clear_launch_watch_state()
            self.state.is_launch_pending = False
            return "timeout"

        return "pending"

    def create_and_start_thread(
        self,
        *,
        parent,
        logger_instance,
        home_sync: Optional[Callable[[object, object], bool]] = None,
        runtime_config=None,
        on_state_changed: Callable[[str], None],
        on_task_completed: Callable[[str], None],
        on_task_started: Callable[[str], None],
        on_task_failed: Callable[[str], None],
        on_show_tray_message: Callable[[str, str], None],
    ) -> Optional[TaskQueueThread]:
        if not self.state.tasks_to_run:
            return None

        thread = TaskQueueThread(
            tasks_to_run=list(self.state.tasks_to_run),
            logger_instance=logger_instance,
            task_registry=self.task_registry,
            home_sync=home_sync,
            runtime_config=runtime_config,
            parent=parent,
        )
        thread.is_running_signal.connect(on_state_changed)
        thread.task_completed_signal.connect(on_task_completed)
        thread.task_started_signal.connect(on_task_started)
        thread.task_failed_signal.connect(on_task_failed)
        thread.show_tray_message_signal.connect(on_show_tray_message)
        thread.start()
        self._start_thread = thread
        return thread

    def stop_running_thread(self, reason: Optional[str] = None) -> bool:
        thread = self._start_thread
        if thread is not None and thread.isRunning():
            thread.stop(reason=reason)
            return True
        return False

    def apply_thread_flag(self, flag: str) -> ThreadTransition:
        transition = ThreadTransition(flag=flag)

        if flag == "start":
            self.state.is_running = True
            self.state.is_launch_pending = False
            transition.started = True
            return transition

        if flag in {"end", "no_auto", "interrupted"}:
            self.state.is_running = False
            self.state.is_launch_pending = False
            self.state.is_running_solo = False
            self.state.is_scheduled_run = False
            transition.stopped = True
            transition.should_after_finish = flag == "end"
        return transition

    def should_stop_for_window_closed(self, game_window_open: bool, current_task_id: str = None) -> bool:
        """核心守卫判定：判断当前任务是否允许窗口关闭"""
        if not self.state.is_running or game_window_open:
            return False
        
        if current_task_id:
            meta = self.task_registry.get(current_task_id, {})
            # 如果当前是置底清理类任务，窗口关闭是预期行为，守卫不应干预
            if meta.get("periodic_role") == "cleanup" or meta.get("force_last"):
                return False
                
        return True
