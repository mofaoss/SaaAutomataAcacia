import os
import time
import win32gui
import win32con

from app.framework.infra.events.signal_bus import signalBus
from app.features.modules.enter_game.usecase.enter_game_usecase import is_snowbreak_running

from app.framework.core.module_system import on_demand_module, periodic_module, Field
from app.framework.i18n import _


@periodic_module(
    "执行退出",
    notify_on_completion=False,
    periodic_requires_home_sync=False,
    periodic_force_last=True,
    periodic_mandatory=True,
    description="### 提示\n* 开启“自动加入计划队列”后，到点自动执行计划任务时，将自动在队列末尾执行本项目以清理环境（如关闭游戏等）。\n* 关闭助手后，计划任务将不会继续执行",
    fields={
        "CheckBox_auto_run": Field("自动加入计划队列"),
        "CheckBox_close_game": Field("退出游戏"),
        "CheckBox_shutdown": Field("关机"),
        "CheckBox_close_proxy": Field("退出助手"),
    }
)
class CloseGameModule:
    def __init__(
        self,
        auto,
        logger,
        app_config,
        CheckBox_auto_run: bool = False,
        CheckBox_close_game: bool = False,
        CheckBox_shutdown: bool = False,
        CheckBox_close_proxy: bool = False,
    ):
        self.auto = auto
        self.logger = logger
        self.app_config = app_config
        self.auto_run_enabled = CheckBox_auto_run
        self.close_game_enabled = CheckBox_close_game
        self.shutdown_enabled = CheckBox_shutdown
        self.close_proxy_enabled = CheckBox_close_proxy

    def run(self):
        # 即使被加入队列，也通过内部逻辑进行最终防护 (目前 dispatcher 会控制加入，这里双重保险)
        self.logger.info(_('Executing exit tasks...', msgid='executing_exit_tasks'))
        
        # 1. 退出游戏
        if self.close_game_enabled:
            self.logger.info(_('Exiting game...', msgid='exiting_game'))
            hwnd = is_snowbreak_running(app_config=self.app_config)
            if hwnd:
                win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                time.sleep(2)

        # 2. 关机
        if self.shutdown_enabled:
            self.logger.info(_('System will shut down in 60s...', msgid='system_will_shut_down_in_60s'))
            os.system("shutdown -s -t 60")

        # 3. 退出代理 (发送信号给主窗口处理)
        if self.close_proxy_enabled:
            self.logger.info(_('Exiting Application...', msgid='exiting_application'))
            signalBus.requestExitApp.emit()
