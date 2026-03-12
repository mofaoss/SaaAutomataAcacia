from app.framework.ui.widgets.custom_message_box import CustomMessageBox


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
                _('One code per line', msgid='one_code_per_line')
            )
            if dialog.exec():
                return dialog.content.toPlainText()
            return None
        finally:
            self._is_dialog_open = False

