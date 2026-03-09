from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout
from qfluentwidgets import BodyLabel, ComboBox, SpinBox

from app.framework.ui.views.periodic_base import ModulePageBase


class OperationPage(ModulePageBase):
    def __init__(self, parent=None):
        super().__init__("page_operation", parent=parent, host_context="periodic", use_default_layout=True)

        self.BodyLabel_7 = BodyLabel(self)
        self.BodyLabel_7.setObjectName("BodyLabel_7")
        self.SpinBox_action_times = SpinBox(self)
        self.SpinBox_action_times.setObjectName("SpinBox_action_times")
        self.SpinBox_action_times.setRange(1, 999)

        self.BodyLabel_22 = BodyLabel(self)
        self.BodyLabel_22.setObjectName("BodyLabel_22")
        self.ComboBox_run = ComboBox(self)
        self.ComboBox_run.setObjectName("ComboBox_run")

        self.BodyLabel_tip_action = BodyLabel(self)
        self.BodyLabel_tip_action.setObjectName("BodyLabel_tip_action")
        self.BodyLabel_tip_action.setTextFormat(Qt.TextFormat.MarkdownText)
        self.BodyLabel_tip_action.setWordWrap(True)

        self.main_layout.addLayout(self._row(self.BodyLabel_7, self.SpinBox_action_times))
        self.main_layout.addLayout(self._row(self.BodyLabel_22, self.ComboBox_run))
        self.main_layout.addWidget(self.BodyLabel_tip_action)
        self._apply_i18n()
        self.finalize()

    def _apply_i18n(self):
        self.BodyLabel_22.setText(self._ui_text("疾跑方式", "Sprint mode"))
        self.BodyLabel_7.setText(self._ui_text("刷取次数", "Run count"))
        self.ComboBox_run.addItems(
            ["Toggle Sprint", "Hold Sprint"]
            if self._is_non_chinese_ui
            else ["切换疾跑", "按住疾跑"]
        )
        self.BodyLabel_tip_action.setText(
            "### Tips\n* Auto-run operation \n* Repeats the first training stage for specified times with no stamina cost\n* Useful for weekly pass mission count"
            if self._is_non_chinese_ui
            else "### 提示\n* 重复刷指定次数无需体力的实战训练第一关\n* 用于完成凭证20次常规行动周常任务"
        )

    @staticmethod
    def _row(label, edit):
        line = QHBoxLayout()
        line.addWidget(label, 1)
        line.addWidget(edit, 2)
        return line
