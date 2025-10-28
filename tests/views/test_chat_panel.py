from __future__ import annotations

from typing import Generator, List, cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QSplitter

from views.chat_panel import ChatPanel


@pytest.fixture(name="qt_app")
def fixture_qt_app() -> Generator[QApplication, None, None]:
    """テスト全体で共有するQApplicationインスタンスを保持する。"""
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    app = cast(QApplication, app_instance)
    yield app


def test_append_messages(qt_app: QApplication) -> None:
    """append系メソッドで履歴が正しく更新されることを検証する。"""
    panel = ChatPanel()

    splitter = panel.findChild(QSplitter, "chatSplitter")
    assert splitter is not None
    assert splitter.orientation() == Qt.Orientation.Vertical

    panel.append_user_message("こんにちは")
    panel.append_ai_message("了解しました")

    history = panel.findChild(QPlainTextEdit, "chatHistory")
    assert history is not None
    assert history.toPlainText().splitlines() == ["ユーザー: こんにちは", "AI: 了解しました"]


def test_request_ai_completion_emits_signal(qt_app: QApplication) -> None:
    """request_ai_completionがシグナルを発行し入力欄をクリアすることを検証する。"""
    panel = ChatPanel()
    captured: List[str] = []
    panel.completion_requested.connect(captured.append)

    input_field = panel.findChild(QPlainTextEdit, "chatInput")
    assert input_field is not None
    input_field.setPlainText("テスト入力")

    result = panel.request_ai_completion()

    assert result == "テスト入力"
    assert captured == ["テスト入力"]
    assert input_field.toPlainText() == ""


def test_request_ai_completion_ignores_empty(qt_app: QApplication) -> None:
    """空文字の場合はシグナルを発行しないことを検証する。"""
    panel = ChatPanel()
    captured: List[str] = []
    panel.completion_requested.connect(captured.append)

    result = panel.request_ai_completion()

    assert result is None
    assert captured == []
