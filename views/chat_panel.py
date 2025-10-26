from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ChatPanel(QWidget):
    """チャットメッセージを表示し、AIへのリクエストを送信するパネル。"""

    completion_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None, *, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(parent)
        self._logger = logger or logging.getLogger("my_editor.chat_panel")
        self._history = QPlainTextEdit(self)
        self._history.setObjectName("chatHistory")
        self._history.setReadOnly(True)
        self._input_field = QPlainTextEdit(self)
        self._input_field.setObjectName("chatInput")
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
        layout.addWidget(self._history)

        input_row = QHBoxLayout()
        input_row.addWidget(self._input_field)
        input_row.addWidget(self._request_button)
        layout.addLayout(input_row)

    def _connect_signals(self) -> None:
        """内部シグナルの接続を行う。"""
        self._request_button.clicked.connect(self.request_ai_completion)

    def _append_message(self, speaker: str, text: str) -> None:
        """スピーカー名付きでメッセージを記録する。"""
        formatted = f"{speaker}: {text}"
        self._history.appendPlainText(formatted)
        self._logger.info("%sメッセージを記録しました。", speaker)

