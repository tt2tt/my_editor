from __future__ import annotations

from collections.abc import Generator
from typing import cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QPushButton, QSplitter

from views.main_window import MainWindow
from views.editor_tab_widget import EditorTabWidget
from views.folder_tree import FolderTree


@pytest.fixture(name="qt_app")
def fixture_qt_app() -> Generator[QApplication, None, None]:
    """テスト全体で共有するQApplicationインスタンスを管理する。"""
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    app = cast(QApplication, app_instance)
    yield app


@pytest.fixture(name="main_window")
def fixture_main_window(qt_app: QApplication) -> Generator[MainWindow, None, None]:
    """メインウィンドウを生成し、テスト後にクリーンアップする。"""
    window = MainWindow()
    yield window
    window.close()
    window.deleteLater()


def test_main_window_builds_layout(main_window: MainWindow) -> None:
    """レイアウトが構築され主要ウィジェットが存在することを検証する。"""
    splitter = main_window.centralWidget().findChild(QSplitter, "mainSplitter")
    assert splitter is not None
    editor_splitter = main_window.centralWidget().findChild(QSplitter, "editorSplitter")
    assert editor_splitter is not None

    folder = main_window.folder_view
    assert isinstance(folder, FolderTree)
    assert isinstance(main_window.tab_widget, EditorTabWidget)
    assert main_window.action_new_file.text() == "新規ファイル"
    assert main_window.action_open_settings.text() == "OpenAI設定..."
    assert main_window.tab_widget.count() == 0


def test_chat_panel_request_triggers_signal(main_window: MainWindow, qt_app: QApplication) -> None:
    """チャットパネルからの送信がシグナルを発行し履歴へ反映されることを検証する。"""
    captured: list[str] = []
    main_window.chat_submitted.connect(captured.append)

    panel = main_window.chat_panel
    input_field = panel.findChild(QPlainTextEdit, "chatInput")
    send_button = panel.findChild(QPushButton, "chatRequestButton")
    history = panel.findChild(QPlainTextEdit, "chatHistory")

    assert input_field is not None
    assert send_button is not None
    assert history is not None

    input_field.setPlainText("hello")
    QTest.mouseClick(send_button, Qt.MouseButton.LeftButton)
    qt_app.processEvents()

    assert captured == ["hello"]
    assert "ユーザー: hello" in history.toPlainText()
