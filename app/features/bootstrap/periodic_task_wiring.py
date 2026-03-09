# coding:utf-8
from __future__ import annotations

import copy

# Periodic host scheduling metadata only.
# UI display names are sourced from module registry (module_specs), not here.
PRIMARY_PERIODIC_TASK_ID = "task_login"

PERIODIC_TASK_SPECS = [
    {
        "id": PRIMARY_PERIODIC_TASK_ID,
        "ui_page_index": 0,
        "option_key": "CheckBox_entry_1",
        "requires_home_sync": False,
        "is_mandatory": True,
        "force_first": True,
        "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
    },
    {
        "id": "task_supplies",
        "ui_page_index": 1,
        "option_key": "CheckBox_stamina_2",
        "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
    },
    {
        "id": "task_shop",
        "ui_page_index": 2,
        "option_key": "CheckBox_shop_3",
        "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
    },
    {
        "id": "task_stamina",
        "ui_page_index": 3,
        "option_key": "CheckBox_use_power_4",
        "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
    },
    {
        "id": "task_shards",
        "ui_page_index": 4,
        "option_key": "CheckBox_person_5",
        "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
    },
    {
        "id": "task_chasm",
        "ui_page_index": 5,
        "option_key": "CheckBox_chasm_6",
        "default_activation_config": [{"type": "weekly", "day": 1, "time": "10:00", "max_runs": 1}],
    },
    {
        "id": "task_reward",
        "ui_page_index": 6,
        "option_key": "CheckBox_reward_7",
        "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
    },
    {
        "id": "task_operation",
        "ui_page_index": 7,
        "option_key": "CheckBox_operation_8",
        "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
    },
    {
        "id": "task_weapon",
        "ui_page_index": 8,
        "option_key": "CheckBox_weapon_8",
        "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
    },
    {
        "id": "task_shard_exchange",
        "ui_page_index": 9,
        "option_key": "CheckBox_shard_exchange_9",
        "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
    },
    {
        "id": "task_close_game",
        "ui_page_index": 10,
        "option_key": "CheckBox_close_game_10",
        "requires_home_sync": False,
        "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
    },
]


def build_default_periodic_task_sequence() -> list[dict]:
    sequence: list[dict] = []
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


__all__ = ["PRIMARY_PERIODIC_TASK_ID", "PERIODIC_TASK_SPECS", "build_default_periodic_task_sequence"]
