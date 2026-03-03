from PySide6.QtWidgets import QGridLayout
from qfluentwidgets import TextEdit


class HelpView:
    def __init__(self, parent):
        self._parent = parent
        self.setup_ui(parent)

    def setup_ui(self, parent):
        parent.setObjectName("help")

        self.gridLayout = QGridLayout(parent)
        self.gridLayout.setContentsMargins(0, 0, 0, -1)
        self.gridLayout.setObjectName("gridLayout")

        self.TextEdit_markdown = TextEdit(parent)
        self.TextEdit_markdown.setEnabled(True)
        self.TextEdit_markdown.setStyleSheet(
            "LineEdit, TextEdit, PlainTextEdit {\n"
            "    color: black;\n"
            "    background-color: rgba(255, 255, 255, 0.7);\n"
            "    border-radius: 5px;\n"
            "    padding: 0px 10px;\n"
            "    selection-background-color: #00a7b3;\n"
            "}\n"
            "\n"
            "TextEdit,\n"
            "PlainTextEdit {\n"
            "    padding: 2px 3px 2px 8px;\n"
            "}\n"
            "\n"
            "LineEdit:disabled, TextEdit:disabled,\n"
            "PlainTextEdit:disabled {\n"
            "    color: rgba(0, 0, 0, 150);\n"
            "    background-color: rgba(249, 249, 249, 0.3);\n"
            "}\n"
        )
        self.TextEdit_markdown.setObjectName("TextEdit_markdown")
        self.gridLayout.addWidget(self.TextEdit_markdown, 0, 0, 1, 1)
