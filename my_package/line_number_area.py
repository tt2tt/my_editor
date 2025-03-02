from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QSize

class LineNumberArea(QWidget):
    def __init__(self, editor):
        """LineNumberAreaの初期化"""
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        """LineNumberAreaのサイズを返す"""
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        """LineNumberAreaの描画イベント"""
        self.editor.line_number_area_paint_event(event)
