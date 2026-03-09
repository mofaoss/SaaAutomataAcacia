from PySide6.QtCore import Qt
from qfluentwidgets import BodyLabel

from app.framework.ui.views.daily_base_page import BaseDailyPage


class RewardPage(BaseDailyPage):
    def __init__(self, parent=None):
        super().__init__("page_reward", parent=parent)

        self.BodyLabel_reward_tip = BodyLabel(self)
        self.BodyLabel_reward_tip.setObjectName("BodyLabel_reward_tip")
        self.BodyLabel_reward_tip.setTextFormat(Qt.TextFormat.MarkdownText)
        self.BodyLabel_reward_tip.setWordWrap(True)

        self.main_layout.addWidget(self.BodyLabel_reward_tip)
        self.finalize()

