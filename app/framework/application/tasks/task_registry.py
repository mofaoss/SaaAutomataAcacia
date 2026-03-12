# coding:utf-8
"""Task registry assembled from the unified module system."""

from app.framework.application.modules import (
    get_on_demand_module_specs,
    get_periodic_module_specs,
)
from app.framework.application.tasks.task_definition import TaskDefinition, TaskDomain


def _build_periodic_tasks() -> list[TaskDefinition]:
    tasks: list[TaskDefinition] = []
    for spec in get_periodic_module_specs():
        bindings = spec.ui_bindings
        tasks.append(
            TaskDefinition(
                id=spec.id,
                module_class=spec.module_class,
                name=spec.name,
                name_msgid=spec.name_msgid,
                domain=TaskDomain.PERIODIC,
                ui_page_index=None,
                option_key=None,
                page_attr=bindings.page_attr if bindings else None,
                requires_home_sync=True,
                is_mandatory=False,
                force_first=False,
            )
        )
    return tasks


def _build_on_demand_tasks() -> list[TaskDefinition]:
    tasks: list[TaskDefinition] = []
    for spec in get_on_demand_module_specs(include_passive=False):
        bindings = spec.ui_bindings
        if bindings is None or spec.module_class is None:
            continue
        tasks.append(
            TaskDefinition(
                id=spec.id,
                module_class=spec.module_class,
                name=spec.name,
                name_msgid=spec.name_msgid,
                domain=TaskDomain.ON_DEMAND,
                page_attr=bindings.page_attr,
                card_widget_attr=bindings.card_widget_attr,
                log_widget_attr=bindings.log_widget_attr,
                start_button_attr=bindings.start_button_attr,
            )
        )
    return tasks


DAILY_TASKS: list[TaskDefinition] = _build_periodic_tasks()
ADDITIONAL_TASKS: list[TaskDefinition] = _build_on_demand_tasks()

DAILY_TASK_REGISTRY = {task.id: task.to_legacy_meta() for task in DAILY_TASKS}
DAILY_TASKS_BY_ID = {task.id: task for task in DAILY_TASKS}
ADDITIONAL_TASKS_BY_ID = {task.id: task for task in ADDITIONAL_TASKS}
