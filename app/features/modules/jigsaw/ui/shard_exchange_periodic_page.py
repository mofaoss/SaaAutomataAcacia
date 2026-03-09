from PySide6.QtCore import Qt
from qfluentwidgets import BodyLabel, CheckBox

from app.framework.ui.views.periodic_base import ModulePageBase


class ShardExchangePage(ModulePageBase):
    def __init__(self, parent=None):
        super().__init__("page_shard_exchange", parent=parent, host_context="periodic", use_default_layout=True)

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
        self.CheckBox_receive_shards.setText(self._ui_text("一键接收", "Auto Receive"))
        self.CheckBox_gift_shards.setText(self._ui_text("一键赠送", "Auto Gift"))
        self.CheckBox_recycle_shards.setText(self._ui_text("智能回收", "Smart Recycle"))
        self.BodyLabel_shard_tip.setText(
            "### Tips\n* Auto receive, gift, and recycle puzzle shards\n* Retains at least 15 of each shard when recycling"
            if self._is_non_chinese_ui
            else "### 提示\n* 自动进行基地信源碎片的接收、赠送和回收\n* 回收时每种碎片默认至少保留15个"
        )

        self.main_layout.addWidget(self.CheckBox_receive_shards)
        self.main_layout.addWidget(self.CheckBox_gift_shards)
        self.main_layout.addWidget(self.CheckBox_recycle_shards)
        self.main_layout.addWidget(self.BodyLabel_shard_tip)
        self.finalize()
