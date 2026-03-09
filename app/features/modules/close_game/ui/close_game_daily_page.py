from qfluentwidgets import CheckBox

from app.framework.ui.views.daily_base_page import BaseDailyPage


class CloseGamePage(BaseDailyPage):
    def __init__(self, parent=None):
        super().__init__("page_close_game", parent=parent)

        self.CheckBox_close_game = CheckBox(self)
        self.CheckBox_close_game.setObjectName("CheckBox_close_game")
        self.CheckBox_close_proxy = CheckBox(self)
        self.CheckBox_close_proxy.setObjectName("CheckBox_close_proxy")
        self.CheckBox_shutdown = CheckBox(self)
        self.CheckBox_shutdown.setObjectName("CheckBox_shutdown")

        self.main_layout.addWidget(self.CheckBox_close_game)
        self.main_layout.addWidget(self.CheckBox_close_proxy)
        self.main_layout.addWidget(self.CheckBox_shutdown)
        self.finalize()

