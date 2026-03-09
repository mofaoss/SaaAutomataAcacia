from PySide6.QtWidgets import QHBoxLayout
from qfluentwidgets import BodyLabel, CheckBox, ComboBox, StrongBodyLabel

from app.framework.ui.views.periodic_base import ModulePageBase


class UsePowerPage(ModulePageBase):
    def __init__(self, parent=None):
        super().__init__("page_2", parent=parent, host_context="periodic", use_default_layout=True)

        first_line = QHBoxLayout()
        self.CheckBox_is_use_power = CheckBox(self)
        self.CheckBox_is_use_power.setObjectName("CheckBox_is_use_power")
        self.ComboBox_power_day = ComboBox(self)
        self.ComboBox_power_day.setObjectName("ComboBox_power_day")
        self.BodyLabel_6 = BodyLabel(self)
        self.BodyLabel_6.setObjectName("BodyLabel_6")
        first_line.addWidget(self.CheckBox_is_use_power)
        first_line.addWidget(self.ComboBox_power_day)
        first_line.addWidget(self.BodyLabel_6)

        self.StrongBodyLabel_2 = StrongBodyLabel(self)
        self.StrongBodyLabel_2.setObjectName("StrongBodyLabel_2")
        self.ComboBox_power_usage = ComboBox(self)
        self.ComboBox_power_usage.setObjectName("ComboBox_power_usage")

        self.main_layout.addLayout(first_line)
        self.main_layout.addWidget(self.StrongBodyLabel_2)
        self.main_layout.addWidget(self.ComboBox_power_usage)
        self._apply_i18n()
        self.finalize()

    def _apply_i18n(self):
        self.ComboBox_power_day.addItems(["1", "2", "3", "4", "5", "6"])
        self.ComboBox_power_usage.addItems(
            [
                self._ui_text("活动材料本", "Event Stages"),
                self._ui_text("刷常规后勤", "Operation Logistics"),
            ]
        )
        self.StrongBodyLabel_2.setText(self._ui_text("选择体力使用方式", "Stamina usage mode"))
        self.CheckBox_is_use_power.setText(self._ui_text("自动使用期限", "Auto use expiring"))
        self.BodyLabel_6.setText(self._ui_text("天内的体力药", "day potion"))
