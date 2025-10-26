from __future__ import annotations

from collections.abc import Generator
from typing import cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QSplitter

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

    folder = main_window.folder_view
    assert isinstance(folder, FolderTree)
    assert isinstance(main_window.tab_widget, EditorTabWidget)
    assert main_window.tab_widget.count() == 0


def test_chat_input_clear_on_send(main_window: MainWindow, qt_app: QApplication) -> None:
    """送信操作でチャット入力がクリアされることを検証する。"""
    main_window.chat_input.setText("hello")
    QTest.mouseClick(main_window.send_button, Qt.MouseButton.LeftButton)
    qt_app.processEvents()
    assert main_window.chat_input.text() == ""
