from PySide6.QtWidgets import QFrame, QTextBrowser, QVBoxLayout, QWidget
from qfluentwidgets import TitleLabel


class TerminalInterface(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setup_ui(self)

    def setup_ui(self, terminal):
        terminal.setObjectName("Terminal")
        terminal.resize(851, 651)

        self.verticalLayoutWidget = QWidget(terminal)
        self.verticalLayoutWidget.setGeometry(0, 0, 851, 651)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")

        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(3, 0, 3, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")

        self.TitleLabel = TitleLabel(self.verticalLayoutWidget)
        self.TitleLabel.setStyleSheet("margin-left: 1px;")
        self.TitleLabel.setObjectName("TitleLabel")
        self.TitleLabel.setText("终端")
        self.verticalLayout.addWidget(self.TitleLabel)

        self.textBrowser = QTextBrowser(self.verticalLayoutWidget)
        self.textBrowser.setStyleSheet(
            "border-radius: 20px;\n"
            "margin-left: 3px;\n"
            "margin-right: 3px;\n"
            "margin-bottom: 6px;"
        )
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout.addWidget(self.textBrowser)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 11)
