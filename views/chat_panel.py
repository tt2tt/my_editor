from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class ChatPanel(QWidget):
    """チャットメッセージを表示し、AIへのリクエストを送信するパネル。"""

    completion_requested = Signal(str)
    attachment_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None, *, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(parent)
        self._logger = logger or logging.getLogger("my_editor.chat_panel")
        self._history = QPlainTextEdit(self)
        self._history.setObjectName("chatHistory")
        self._history.setReadOnly(True)
        self._history.setMinimumHeight(80)
        self._input_field = QPlainTextEdit(self)
        self._input_field.setObjectName("chatInput")
        self._attach_button = QPushButton("ファイル添付", self)
        self._attach_button.setObjectName("chatAttachButton")
        self._request_button = QPushButton("送信", self)
        self._request_button.setObjectName("chatRequestButton")

        self._build_layout()
        self._connect_signals()

    def append_user_message(self, text: str) -> None:
        """ユーザーからのメッセージを履歴に追加する。"""
        self._append_message("ユーザー", text)

    def append_ai_message(self, text: str) -> None:
        """AIからのメッセージを履歴に追加する。"""
        self._append_message("AI", text)

    def request_ai_completion(self) -> Optional[str]:
        """入力欄の内容をAI補完リクエストとして送信する。"""
        message = self._input_field.toPlainText().strip()
        if not message:
            self._logger.warning("チャット送信内容が空のためリクエストを棄却しました。")
            return None

        self._input_field.clear()
        self.completion_requested.emit(message)
        self._logger.info("AI補完リクエストを送信しました。")
        return message

    def _build_layout(self) -> None:
        """ウィジェット構成を初期化する。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.setObjectName("chatSplitter")

        splitter.addWidget(self._history)

        input_container = QWidget(splitter)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(4)
        input_layout.addWidget(self._input_field)
        input_layout.addWidget(self._attach_button)
        input_layout.addWidget(self._request_button)

        splitter.addWidget(input_container)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)
        self._splitter = splitter

    def _connect_signals(self) -> None:
        """内部シグナルの接続を行う。"""
        self._request_button.clicked.connect(self.request_ai_completion)
        self._attach_button.clicked.connect(self.request_file_attachment)

    def _append_message(self, speaker: str, text: str) -> None:
        """スピーカー名付きでメッセージを記録する。"""
        formatted = f"{speaker}: {text}"
        self._history.appendPlainText(formatted)
        self._logger.info("%sメッセージを記録しました。", speaker)

    def request_file_attachment(self) -> None:
        """ファイル添付ボタンの操作を通知する。"""
        self.attachment_requested.emit()
        self._logger.info("チャット添付リクエストを送信しました。")

