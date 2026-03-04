import os

from PySide6.QtWidgets import QFrame, QGridLayout
from qfluentwidgets import TextBrowser

from app.common.config import is_non_chinese_ui_language
from app.common.style_sheet import StyleSheet


class Help(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._is_non_chinese_ui = is_non_chinese_ui_language()
        self.setObjectName(text.replace(' ', '-'))

        # 1. 搭建骨架 (原 View 的职责)
        self._setup_ui()
        # 2. 填充内容 (原 Controller 的职责)
        self._load_markdown()
        # 3. 穿上衣服
        StyleSheet.HELP_INTERFACE.apply(self)

    def _setup_ui(self):
        """负责创建和布局控件"""
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, -1)
        self.gridLayout.setObjectName("gridLayout")

        self.TextEdit_markdown = TextBrowser(self)
        self.TextEdit_markdown.setObjectName("TextEdit_markdown")
        # 允许外部超链接跳转
        self.TextEdit_markdown.setOpenExternalLinks(True)

        self.gridLayout.addWidget(self.TextEdit_markdown, 0, 0, 1, 1)

    def _load_markdown(self):
        """负责加载业务数据"""
        markdown_path = './docs/help_en.md' if self._is_non_chinese_ui else './docs/help.md'

        # 兜底逻辑：如果英文文档不存在，回退到中文文档
        if not os.path.exists(markdown_path):
            markdown_path = './docs/help.md'

        try:
            with open(markdown_path, 'r', encoding='utf-8') as file:
                text = file.read()
                self.TextEdit_markdown.setMarkdown(text)
        except Exception as e:
            self.TextEdit_markdown.setMarkdown(f"### 加载帮助文档失败\n\n{e}")