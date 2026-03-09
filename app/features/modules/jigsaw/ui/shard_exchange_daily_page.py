from PySide6.QtCore import Qt
from qfluentwidgets import BodyLabel, CheckBox

from app.framework.ui.views.daily_base_page import BaseDailyPage


class ShardExchangePage(BaseDailyPage):
    def __init__(self, parent=None):
        super().__init__("page_shard_exchange", parent=parent)

        self.CheckBox_receive_shards = CheckBox(self)
        self.CheckBox_receive_shards.setObjectName("enable_receive_shards")

        self.CheckBox_gift_shards = CheckBox(self)
        self.CheckBox_gift_shards.setObjectName("enable_gift_shards")

        self.CheckBox_recycle_shards = CheckBox(self)
        self.CheckBox_recycle_shards.setObjectName("enable_recycle_shards")

        self.BodyLabel_shard_tip = BodyLabel(self)
        self.BodyLabel_shard_tip.setObjectName("BodyLabel_shard_tip")
        self.BodyLabel_shard_tip.setTextFormat(Qt.TextFormat.MarkdownText)
        self.BodyLabel_shard_tip.setWordWrap(True)

        self.main_layout.addWidget(self.CheckBox_receive_shards)
        self.main_layout.addWidget(self.CheckBox_gift_shards)
        self.main_layout.addWidget(self.CheckBox_recycle_shards)
        self.main_layout.addWidget(self.BodyLabel_shard_tip)
        self.finalize()

