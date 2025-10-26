from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QResizeEvent, QWheelEvent, QTextCharFormat, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget


class _LineNumberArea(QWidget):
    """エディタ左側に行番号を描画する補助ウィジェット。"""

    def __init__(self, editor: EditorWidget) -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:  # pragma: no cover - Qt内部で利用
        return QSize(self._editor._line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent) -> None:  # pragma: no cover - Qt内でハンドル
        self._editor._paint_line_numbers(event)


class EditorWidget(QPlainTextEdit):
    """コード編集用に行番号とズーム操作を備えたエディタウィジェット。"""

    def __init__(self, parent: QWidget | None = None, *, logger: logging.Logger | None = None) -> None:
        super().__init__(parent)
        # 操作用ロガーとズームレベルを保持する。
        self._logger = logger or logging.getLogger("my_editor.editor_widget")
        self._line_number_area = _LineNumberArea(self)
        self._current_zoom = 0

        self._init_line_numbers()

    def _init_line_numbers(self) -> None:
        """行番号領域の初期設定とシグナル接続を行う。"""
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._update_line_number_area_width(0)
        self._highlight_current_line()
        self._logger.debug("行番号領域を初期化しました。")

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Ctrl+ホイールでズーム、それ以外は標準動作とする。"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            if angle > 0:
                self._apply_zoom(1)
            elif angle < 0:
                self._apply_zoom(-1)
            event.accept()
            return
        super().wheelEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:  # pragma: no cover - Qt内部で利用
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height()))

    def _line_number_area_width(self) -> int:
        """現在の行数に基づき行番号領域の幅を算出する。"""
        digits = max(1, len(str(max(1, self.blockCount()))))
        space = 3 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def _update_line_number_area_width(self, _new_block_count: int) -> None:
        """行数変化に応じてマージンを更新する。"""
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        """スクロール時に行番号領域を再描画する。"""
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.top(), self._line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def _paint_line_numbers(self, event: QPaintEvent) -> None:
        """行番号領域へ行番号を描画する。"""
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor(45, 45, 50))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(220, 220, 225))
                painter.drawText(0, top, self._line_number_area.width() - 4, self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            block_number += 1
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())

    def _highlight_current_line(self) -> None:
        """選択行を背景色で強調表示する。"""
        selection_any: Any = QTextEdit.ExtraSelection()
        line_color = QColor(55, 70, 90)
        char_format = QTextCharFormat()
        char_format.setBackground(line_color)
        char_format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        char_format.setForeground(QColor(240, 240, 245))
        selection_any.format = char_format
        cursor = self.textCursor()
        cursor.clearSelection()
        selection_any.cursor = cursor
        self.setExtraSelections([selection_any])

    def _apply_zoom(self, step: int) -> None:
        """ズーム量を更新しエディタへ反映する。"""
        self._current_zoom += step
        if step > 0:
            self.zoomIn(step)
        else:
            self.zoomOut(-step)
        self._logger.debug("ズームを更新しました: %s", self._current_zoom)

    @property
    def current_zoom_level(self) -> int:
        """現在のズームレベルを返す。"""
        return self._current_zoom
