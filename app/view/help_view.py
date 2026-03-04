from PySide6.QtWidgets import QGridLayout
from qfluentwidgets import TextBrowser

class HelpView:
    def __init__(self, parent):
        self._parent = parent
        self.setup_ui(parent)

    def setup_ui(self, parent):
        parent.setObjectName("help")

        self.gridLayout = QGridLayout(parent)
        self.gridLayout.setContentsMargins(0, 0, 0, -1)
        self.gridLayout.setObjectName("gridLayout")
        self.TextEdit_markdown = TextBrowser(parent)
        self.TextEdit_markdown.setObjectName("TextEdit_markdown")
        self.TextEdit_markdown.setOpenExternalLinks(True)
        self.gridLayout.addWidget(self.TextEdit_markdown, 0, 0, 1, 1)
