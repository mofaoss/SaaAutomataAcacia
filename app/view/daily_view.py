from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QTextBrowser,
)
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    LineEdit,
    PopUpAniStackedWidget,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SimpleCardWidget,
    StrongBodyLabel,
    TitleLabel,
    ToolButton,
)


class BaseDailyPage(QWidget):
    def __init__(self, object_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

    def finalize(self):
        self.main_layout.addStretch(1)


class EnterGamePage(BaseDailyPage):
    def __init__(self, parent=None):
        super().__init__("page_5", parent)

        top_line = QHBoxLayout()
        self.StrongBodyLabel_4 = StrongBodyLabel(self)
        self.StrongBodyLabel_4.setObjectName("StrongBodyLabel_4")
        self.PrimaryPushButton_path_tutorial = PrimaryPushButton(self)
        self.PrimaryPushButton_path_tutorial.setObjectName("PrimaryPushButton_path_tutorial")
        top_line.addWidget(self.StrongBodyLabel_4)
        top_line.addWidget(self.PrimaryPushButton_path_tutorial)

        self.LineEdit_game_directory = LineEdit(self)
        self.LineEdit_game_directory.setEnabled(False)
        self.LineEdit_game_directory.setObjectName("LineEdit_game_directory")

        action_line = QHBoxLayout()
        self.CheckBox_open_game_directly = CheckBox(self)
        self.CheckBox_open_game_directly.setObjectName("CheckBox_open_game_directly")
        self.PushButton_select_directory = PushButton(self)
        self.PushButton_select_directory.setObjectName("PushButton_select_directory")
        action_line.addWidget(self.CheckBox_open_game_directly, 1)
        action_line.addWidget(self.PushButton_select_directory)

        self.BodyLabel_enter_tip = BodyLabel(self)
        self.BodyLabel_enter_tip.setObjectName("BodyLabel_enter_tip")
        self.BodyLabel_enter_tip.setText("")
        self.BodyLabel_enter_tip.setTextFormat(Qt.TextFormat.MarkdownText)
        self.BodyLabel_enter_tip.setWordWrap(True)

        self.main_layout.addLayout(top_line)
        self.main_layout.addWidget(self.LineEdit_game_directory)
        self.main_layout.addLayout(action_line)
        self.main_layout.addWidget(self.BodyLabel_enter_tip)
        self.finalize()


class CollectSuppliesPage(BaseDailyPage):
    def __init__(self, parent=None):
        super().__init__("page_3", parent)

        self.CheckBox_mail = CheckBox(self)
        self.CheckBox_mail.setObjectName("CheckBox_mail")
        self.CheckBox_fish_bait = CheckBox(self)
        self.CheckBox_fish_bait.setObjectName("CheckBox_fish_bait")
        self.CheckBox_dormitory = CheckBox(self)
        self.CheckBox_dormitory.setObjectName("CheckBox_dormitory")

        redeem_line = QHBoxLayout()
        self.CheckBox_redeem_code = CheckBox(self)
        self.CheckBox_redeem_code.setObjectName("CheckBox_redeem_code")
        self.PrimaryPushButton_import_codes = PrimaryPushButton(self)
        self.PrimaryPushButton_import_codes.setObjectName("PrimaryPushButton_import_codes")
        self.PushButton_reset_codes = PushButton(self)
        self.PushButton_reset_codes.setObjectName("PushButton_reset_codes")
        redeem_line.addWidget(self.CheckBox_redeem_code, 1)
        redeem_line.addWidget(self.PrimaryPushButton_import_codes)
        redeem_line.addWidget(self.PushButton_reset_codes)

        self.textBrowser_import_codes = QTextBrowser(self)
        self.textBrowser_import_codes.setObjectName("textBrowser_import_codes")
        self.textBrowser_import_codes.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.textBrowser_import_codes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.BodyLabel_collect_supplies = BodyLabel(self)
        self.BodyLabel_collect_supplies.setObjectName("BodyLabel_collect_supplies")
        self.BodyLabel_collect_supplies.setTextFormat(Qt.TextFormat.MarkdownText)
        self.BodyLabel_collect_supplies.setWordWrap(True)

        self.main_layout.addWidget(self.CheckBox_mail)
        self.main_layout.addWidget(self.CheckBox_fish_bait)
        self.main_layout.addWidget(self.CheckBox_dormitory)
        self.main_layout.addLayout(redeem_line)
        self.main_layout.addWidget(self.textBrowser_import_codes)
        self.main_layout.addWidget(self.BodyLabel_collect_supplies)
        self.finalize()


class ShopPage(BaseDailyPage):
    def __init__(self, parent=None):
        super().__init__("page_shop", parent)

        self.ScrollArea = ScrollArea(self)
        self.ScrollArea.setObjectName("ScrollArea")
        self.ScrollArea.setWidgetResizable(True)

        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")

        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        self.StrongBodyLabel = StrongBodyLabel(self.scrollAreaWidgetContents)
        self.StrongBodyLabel.setObjectName("StrongBodyLabel")
        self.gridLayout.addWidget(self.StrongBodyLabel, 0, 0, 1, 1)

        self.widget_2 = QWidget(self.scrollAreaWidgetContents)
        self.widget_2.setObjectName("widget_2")
        self.gridLayout.addWidget(self.widget_2, 1, 0, 1, 1)

        self.widget = QWidget(self.scrollAreaWidgetContents)
        self.widget.setObjectName("widget")
        self.gridLayout.addWidget(self.widget, 2, 0, 1, 1)

        buy_names = [
            "CheckBox_buy_3", "CheckBox_buy_4", "CheckBox_buy_5",
            "CheckBox_buy_6", "CheckBox_buy_7", "CheckBox_buy_8",
            "CheckBox_buy_9", "CheckBox_buy_10", "CheckBox_buy_11",
            "CheckBox_buy_12", "CheckBox_buy_13", "CheckBox_buy_14", "CheckBox_buy_15",
        ]

        row = 4
        for name in buy_names:
            checkbox = CheckBox(self.scrollAreaWidgetContents)
            checkbox.setObjectName(name)
            checkbox.setMinimumSize(QSize(29, 22))
            setattr(self, name, checkbox)
            self.gridLayout.addWidget(checkbox, row, 0, 1, 1)
            row += 1

        self.ScrollArea.setWidget(self.scrollAreaWidgetContents)
        self.main_layout.addWidget(self.ScrollArea)
        self.finalize()


class UsePowerPage(BaseDailyPage):
    def __init__(self, parent=None):
        super().__init__("page_2", parent)

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
        self.finalize()


class PersonPage(BaseDailyPage):
    def __init__(self, parent=None):
        super().__init__("page_4", parent)

        self.StrongBodyLabel_3 = StrongBodyLabel(self)
        self.StrongBodyLabel_3.setObjectName("StrongBodyLabel_3")

        self.BodyLabel_3 = BodyLabel(self)
        self.BodyLabel_3.setObjectName("BodyLabel_3")
        self.LineEdit_c1 = LineEdit(self)
        self.LineEdit_c1.setObjectName("LineEdit_c1")

        self.BodyLabel_4 = BodyLabel(self)
        self.BodyLabel_4.setObjectName("BodyLabel_4")
        self.LineEdit_c2 = LineEdit(self)
        self.LineEdit_c2.setObjectName("LineEdit_c2")

        self.BodyLabel_5 = BodyLabel(self)
        self.BodyLabel_5.setObjectName("BodyLabel_5")
        self.LineEdit_c3 = LineEdit(self)
        self.LineEdit_c3.setObjectName("LineEdit_c3")

        self.BodyLabel_8 = BodyLabel(self)
        self.BodyLabel_8.setObjectName("BodyLabel_8")
        self.LineEdit_c4 = LineEdit(self)
        self.LineEdit_c4.setObjectName("LineEdit_c4")

        self.CheckBox_is_use_chip = CheckBox(self)
        self.CheckBox_is_use_chip.setObjectName("CheckBox_is_use_chip")

        self.BodyLabel_person_tip = BodyLabel(self)
        self.BodyLabel_person_tip.setObjectName("BodyLabel_person_tip")
        self.BodyLabel_person_tip.setTextFormat(Qt.TextFormat.MarkdownText)
        self.BodyLabel_person_tip.setWordWrap(True)

        self.main_layout.addWidget(self.StrongBodyLabel_3)
        self.main_layout.addLayout(self._line(self.BodyLabel_3, self.LineEdit_c1))
        self.main_layout.addLayout(self._line(self.BodyLabel_4, self.LineEdit_c2))
        self.main_layout.addLayout(self._line(self.BodyLabel_5, self.LineEdit_c3))
        self.main_layout.addLayout(self._line(self.BodyLabel_8, self.LineEdit_c4))
        self.main_layout.addWidget(self.CheckBox_is_use_chip)
        self.main_layout.addWidget(self.BodyLabel_person_tip)
        self.finalize()

    @staticmethod
    def _line(label: BodyLabel, edit: LineEdit) -> QHBoxLayout:
        line = QHBoxLayout()
        line.addWidget(label, 1)
        line.addWidget(edit, 2)
        return line


class DailyView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("daily")

        self.gridLayout_2 = QGridLayout(self)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setSpacing(0)

        self._build_option_card()
        self._build_action_card()
        self._build_setting_card()
        self._build_log_card()
        self._build_tips_card()

        self.gridLayout_2.setRowStretch(0, 2)
        self.gridLayout_2.setRowStretch(1, 1)

    def _build_option_card(self):
        self.SimpleCardWidget_option = SimpleCardWidget(self)
        self.SimpleCardWidget_option.setObjectName("SimpleCardWidget_option")
        self.SimpleCardWidget_option.setMinimumSize(QSize(237, 320))

        layout = QVBoxLayout(self.SimpleCardWidget_option)
        layout.setContentsMargins(9, 9, 9, 9)
        layout.setSpacing(6)

        option_rows = [
            ("CheckBox_entry_1", "ToolButton_entry", True),
            ("CheckBox_stamina_2", "ToolButton_collect", True),
            ("CheckBox_shop_3", "ToolButton_shop", True),
            ("CheckBox_use_power_4", "ToolButton_use_power", True),
            ("CheckBox_person_5", "ToolButton_person", True),
            ("CheckBox_chasm_6", "ToolButton_chasm", False),
            ("CheckBox_reward_7", "ToolButton_reward", False),
        ]

        for checkbox_name, button_name, enabled in option_rows:
            row = QHBoxLayout()
            checkbox = CheckBox(self.SimpleCardWidget_option)
            checkbox.setObjectName(checkbox_name)
            button = ToolButton(self.SimpleCardWidget_option)
            button.setObjectName(button_name)
            button.setEnabled(enabled)
            setattr(self, checkbox_name, checkbox)
            setattr(self, button_name, button)
            row.addWidget(checkbox, 1)
            row.addWidget(button)
            layout.addLayout(row)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.PushButton_select_all = PushButton(self.SimpleCardWidget_option)
        self.PushButton_select_all.setObjectName("PushButton_select_all")
        self.PushButton_no_select = PushButton(self.SimpleCardWidget_option)
        self.PushButton_no_select.setObjectName("PushButton_no_select")
        btn_row.addWidget(self.PushButton_select_all)
        btn_row.addWidget(self.PushButton_no_select)
        layout.addSpacing(6)
        layout.addLayout(btn_row)
        layout.addStretch(1)

        self.gridLayout_2.addWidget(self.SimpleCardWidget_option, 0, 0, 1, 1)

    def _build_action_card(self):
        self.SimpleCardWidget_3 = SimpleCardWidget(self)
        self.SimpleCardWidget_3.setObjectName("SimpleCardWidget_3")
        self.SimpleCardWidget_3.setMinimumSize(QSize(237, 165))

        layout = QVBoxLayout(self.SimpleCardWidget_3)
        self.BodyLabel = BodyLabel(self.SimpleCardWidget_3)
        self.BodyLabel.setObjectName("BodyLabel")
        self.ComboBox_after_use = ComboBox(self.SimpleCardWidget_3)
        self.ComboBox_after_use.setObjectName("ComboBox_after_use")
        self.PushButton_start = PushButton(self.SimpleCardWidget_3)
        self.PushButton_start.setObjectName("PushButton_start")
        self.PushButton_start.setMinimumSize(QSize(0, 60))
        self.PushButton_start.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))

        layout.addStretch(1)
        layout.addWidget(self.BodyLabel)
        layout.addWidget(self.ComboBox_after_use)
        layout.addStretch(1)
        layout.addWidget(self.PushButton_start)
        layout.addStretch(1)

        self.gridLayout_2.addWidget(self.SimpleCardWidget_3, 1, 0, 1, 1)

    def _build_setting_card(self):
        self.SimpleCardWidget_2 = SimpleCardWidget(self)
        self.SimpleCardWidget_2.setObjectName("SimpleCardWidget_2")
        self.SimpleCardWidget_2.setMinimumSize(QSize(237, 320))

        layout = QVBoxLayout(self.SimpleCardWidget_2)
        layout.setSpacing(4)

        self.TitleLabel_setting = TitleLabel(self.SimpleCardWidget_2)
        self.TitleLabel_setting.setObjectName("TitleLabel_setting")

        self.PopUpAniStackedWidget = PopUpAniStackedWidget(self.SimpleCardWidget_2)
        self.PopUpAniStackedWidget.setObjectName("PopUpAniStackedWidget")

        self.page_enter = EnterGamePage(self.PopUpAniStackedWidget)
        self.page_collect = CollectSuppliesPage(self.PopUpAniStackedWidget)
        self.page_shop = ShopPage(self.PopUpAniStackedWidget)
        self.page_use_power = UsePowerPage(self.PopUpAniStackedWidget)
        self.page_person = PersonPage(self.PopUpAniStackedWidget)

        self.PopUpAniStackedWidget.addWidget(self.page_enter)
        self.PopUpAniStackedWidget.addWidget(self.page_collect)
        self.PopUpAniStackedWidget.addWidget(self.page_shop)
        self.PopUpAniStackedWidget.addWidget(self.page_use_power)
        self.PopUpAniStackedWidget.addWidget(self.page_person)

        layout.addWidget(self.TitleLabel_setting)
        layout.addWidget(self.PopUpAniStackedWidget)

        self.gridLayout_2.addWidget(self.SimpleCardWidget_2, 0, 1, 1, 1)

        self._alias_page_widgets()

    def _alias_page_widgets(self):
        page_attrs = [
            # enter
            "StrongBodyLabel_4", "PrimaryPushButton_path_tutorial", "CheckBox_open_game_directly",
            "LineEdit_game_directory", "PushButton_select_directory", "BodyLabel_enter_tip",
            # collect
            "CheckBox_mail", "CheckBox_redeem_code", "CheckBox_dormitory", "CheckBox_fish_bait",
            "PushButton_reset_codes", "PrimaryPushButton_import_codes", "textBrowser_import_codes",
            "BodyLabel_collect_supplies",
            # shop
            "ScrollArea", "scrollAreaWidgetContents", "gridLayout", "StrongBodyLabel", "widget", "widget_2",
            "CheckBox_buy_3", "CheckBox_buy_4", "CheckBox_buy_5", "CheckBox_buy_6", "CheckBox_buy_7",
            "CheckBox_buy_8", "CheckBox_buy_9", "CheckBox_buy_10", "CheckBox_buy_11", "CheckBox_buy_12",
            "CheckBox_buy_13", "CheckBox_buy_14", "CheckBox_buy_15",
            # use power
            "ComboBox_power_usage", "StrongBodyLabel_2", "CheckBox_is_use_power", "ComboBox_power_day", "BodyLabel_6",
            # person
            "BodyLabel_8", "LineEdit_c4", "BodyLabel_person_tip", "BodyLabel_5", "LineEdit_c3",
            "CheckBox_is_use_chip", "BodyLabel_3", "LineEdit_c1", "StrongBodyLabel_3", "BodyLabel_4", "LineEdit_c2",
        ]

        pages = [self.page_enter, self.page_collect, self.page_shop, self.page_use_power, self.page_person]
        for attr in page_attrs:
            for page in pages:
                if hasattr(page, attr):
                    setattr(self, attr, getattr(page, attr))
                    break

    def _build_log_card(self):
        self.SimpleCardWidget = SimpleCardWidget(self)
        self.SimpleCardWidget.setObjectName("SimpleCardWidget")
        self.SimpleCardWidget.setMinimumSize(QSize(246, 485))

        layout = QVBoxLayout(self.SimpleCardWidget)
        layout.setSpacing(4)

        self.TitleLabel = TitleLabel(self.SimpleCardWidget)
        self.TitleLabel.setObjectName("TitleLabel")
        self.textBrowser_log = QTextBrowser(self.SimpleCardWidget)
        self.textBrowser_log.setObjectName("textBrowser_log")
        self.textBrowser_log.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        layout.addWidget(self.TitleLabel)
        layout.addWidget(self.textBrowser_log)

        self.gridLayout_2.addWidget(self.SimpleCardWidget, 0, 2, 1, 1)

    def _build_tips_card(self):
        self.SimpleCardWidget_tips = SimpleCardWidget(self)
        self.SimpleCardWidget_tips.setObjectName("SimpleCardWidget_tips")
        self.SimpleCardWidget_tips.setMinimumSize(QSize(237, 165))

        layout = QVBoxLayout(self.SimpleCardWidget_tips)
        layout.setSpacing(3)

        self.TitleLabel_3 = TitleLabel(self.SimpleCardWidget_tips)
        self.TitleLabel_3.setObjectName("TitleLabel_3")
        self.ScrollArea_tips = ScrollArea(self.SimpleCardWidget_tips)
        self.ScrollArea_tips.setObjectName("ScrollArea_tips")
        self.ScrollArea_tips.setWidgetResizable(True)

        self.scrollAreaWidgetContents_tips = QWidget()
        self.scrollAreaWidgetContents_tips.setObjectName("scrollAreaWidgetContents_tips")
        self.gridLayout_tips = QGridLayout(self.scrollAreaWidgetContents_tips)
        self.gridLayout_tips.setObjectName("gridLayout_tips")
        self.gridLayout_tips.setContentsMargins(0, 0, 0, 0)

        self.ScrollArea_tips.setWidget(self.scrollAreaWidgetContents_tips)

        layout.addWidget(self.TitleLabel_3)
        layout.addWidget(self.ScrollArea_tips)

        self.gridLayout_2.addWidget(self.SimpleCardWidget_tips, 1, 2, 1, 1)
