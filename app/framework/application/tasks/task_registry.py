# coding:utf-8
from app.features.modules.alien_guardian.usecase.alien_guardian_usecase import AlienGuardianModule
from app.features.modules.capture_pals.usecase.capture_pals_usecase import CapturePalsModule
from app.features.modules.chasm.usecase.chasm_usecase import ChasmModule
from app.features.modules.close_game.usecase.close_game_usecase import CloseGameModule
from app.features.modules.collect_supplies.usecase.collect_supplies_usecase import CollectSuppliesModule
from app.features.modules.drink.usecase.drink_usecase import DrinkModule
from app.features.modules.enter_game.usecase.enter_game_usecase import EnterGameModule
from app.features.modules.fishing.usecase.fishing_usecase import FishingModule
from app.features.modules.get_reward.usecase.get_reward_usecase import GetRewardModule
from app.features.modules.jigsaw.usecase.shard_exchange_usecase import ShardExchangeModule
from app.features.modules.maze.usecase.maze_usecase import MazeModule
from app.features.modules.operation_action.usecase.operation_usecase import OperationModule
from app.features.modules.person.usecase.person_usecase import PersonModule
from app.features.modules.shopping.usecase.shopping_usecase import ShoppingModule
from app.features.modules.upgrade.usecase.weapon_upgrade_usecase import WeaponUpgradeModule
from app.features.modules.use_power.usecase.use_power_usecase import UsePowerModule
from app.features.modules.water_bomb.usecase.water_bomb_usecase import WaterBombModule

from app.framework.application.tasks.task_definition import TaskDefinition, TaskDomain
from app.framework.application.tasks.periodic_task_specs import PERIODIC_TASK_SPECS


_PERIODIC_MODULE_CLASS_BY_TASK_ID = {
    "task_login": EnterGameModule,
    "task_supplies": CollectSuppliesModule,
    "task_shop": ShoppingModule,
    "task_stamina": UsePowerModule,
    "task_shards": PersonModule,
    "task_chasm": ChasmModule,
    "task_reward": GetRewardModule,
    "task_operation": OperationModule,
    "task_weapon": WeaponUpgradeModule,
    "task_shard_exchange": ShardExchangeModule,
    "task_close_game": CloseGameModule,
}

DAILY_TASKS: list[TaskDefinition] = [
    TaskDefinition(
        id=spec["id"],
        module_class=_PERIODIC_MODULE_CLASS_BY_TASK_ID[spec["id"]],
        zh_name=spec["zh_name"],
        en_name=spec["en_name"],
        domain=TaskDomain.DAILY,
        ui_page_index=spec.get("ui_page_index"),
        option_key=spec.get("option_key"),
        requires_home_sync=spec.get("requires_home_sync", True),
        is_mandatory=spec.get("is_mandatory", False),
        force_first=spec.get("force_first", False),
    )
    for spec in PERIODIC_TASK_SPECS
]

ADDITIONAL_TASKS: list[TaskDefinition] = [
    TaskDefinition("fishing", FishingModule, "钓鱼", "Fishing", TaskDomain.ADDITIONAL, page_attr="page_fishing", card_widget_attr="SimpleCardWidget_fish", log_widget_attr="textBrowser_log_fishing", start_button_attr="PushButton_start_fishing"),
    TaskDefinition("action", OperationModule, "常规训练", "Operation", TaskDomain.ADDITIONAL, page_attr="page_action", card_widget_attr="SimpleCardWidget_action", log_widget_attr="textBrowser_log_action", start_button_attr="PushButton_start_action"),
    TaskDefinition("water_bomb", WaterBombModule, "心动水弹", "Water Bomb", TaskDomain.ADDITIONAL, page_attr="page_water_bomb", card_widget_attr="SimpleCardWidget_water_bomb", log_widget_attr="textBrowser_log_water_bomb", start_button_attr="PushButton_start_water_bomb"),
    TaskDefinition("alien_guardian", AlienGuardianModule, "异星守护", "Alien Guardian", TaskDomain.ADDITIONAL, page_attr="page_alien_guardian", card_widget_attr="SimpleCardWidget_alien_guardian", log_widget_attr="textBrowser_log_alien_guardian", start_button_attr="PushButton_start_alien_guardian"),
    TaskDefinition("maze", MazeModule, "迷宫", "Maze", TaskDomain.ADDITIONAL, page_attr="page_maze", card_widget_attr="SimpleCardWidget_maze", log_widget_attr="textBrowser_log_maze", start_button_attr="PushButton_start_maze"),
    TaskDefinition("drink", DrinkModule, "喝酒", "Drink", TaskDomain.ADDITIONAL, page_attr="page_card", card_widget_attr="SimpleCardWidget_card", log_widget_attr="textBrowser_log_drink", start_button_attr="PushButton_start_drink"),
    TaskDefinition("capture_pals", CapturePalsModule, "抓帕鲁", "Capture Pals", TaskDomain.ADDITIONAL, page_attr="page_capture_pals", card_widget_attr="SimpleCardWidget_capture_pals", log_widget_attr="textBrowser_log_capture_pals", start_button_attr="PushButton_start_capture_pals"),
]


DAILY_TASK_REGISTRY = {task.id: task.to_legacy_meta() for task in DAILY_TASKS}
DAILY_TASKS_BY_ID = {task.id: task for task in DAILY_TASKS}
ADDITIONAL_TASKS_BY_ID = {task.id: task for task in ADDITIONAL_TASKS}
