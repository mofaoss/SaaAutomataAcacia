from app.framework.ui.widgets.custom_message_box import CustomMessageBox
from app.framework.i18n import tr


class RedeemCodesView:
    def __init__(self):
        self._is_dialog_open = False

    def prompt_import_codes(self, parent):
        if self._is_dialog_open:
            return None

        self._is_dialog_open = True
        try:
            dialog = CustomMessageBox(parent, "导入兑换码", "text_edit")
            dialog.content.setEnabled(True)
            dialog.content.setPlaceholderText(
                tr("module.redeem_codes.legacy.8271d40248dc", fallback="One code per line")
            )
            if dialog.exec():
                return dialog.content.toPlainText()
            return None
        finally:
            self._is_dialog_open = False
