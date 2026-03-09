# coding:utf-8
import copy

from app.framework.application.tasks.periodic_task_specs import PERIODIC_TASK_SPECS


def build_default_periodic_task_sequence():
    sequence = []
    for spec in PERIODIC_TASK_SPECS:
        sequence.append(
            {
                "id": spec["id"],
                "enabled": False,
                "use_periodic": False,
                "last_run": 0,
                "activation_config": copy.deepcopy(spec["default_activation_config"]),
                "execution_config": [],
            }
        )
    return sequence
