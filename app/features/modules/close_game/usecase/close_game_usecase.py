import os
import time
import win32gui
import win32con

from app.framework.infra.events.signal_bus import signalBus
from app.features.modules.enter_game.usecase.enter_game_usecase import is_snowbreak_running

from app.framework.core.module_system import on_demand_module, periodic_module, Field
from app.framework.i18n import _


@periodic_module(
    "Execute Exit",
    description="### Tips\n"
                "* Closes the game, proxy, or shuts down the system after all tasks are completed.",
    fields={
        "CheckBox_close_game": Field("Exit Game"),
        "CheckBox_shutdown": Field("Shutdown System"),
        "CheckBox_close_proxy": Field("Exit Application"),
    }
)
class CloseGameModule:
    def __init__(
        self,
        auto,
        logger,
        CheckBox_close_game: bool = False,
        CheckBox_shutdown: bool = False,
        CheckBox_close_proxy: bool = False,
    ):
        self.auto = auto
        self.logger = logger
        self.close_game_enabled = bool(CheckBox_close_game)
        self.shutdown_enabled = bool(CheckBox_shutdown)
        self.close_proxy_enabled = bool(CheckBox_close_proxy)

    def run(self):
        # 1. 退出游戏
        if self.close_game_enabled:
            self.logger.info(_('Exiting game...', msgid='exiting_game'))
            hwnd = is_snowbreak_running()
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


