from PySide6.QtWidgets import QVBoxLayout, QWidget


class BaseDailyPage(QWidget):
    def __init__(self, object_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

    def finalize(self):
        self.main_layout.addStretch(1)

