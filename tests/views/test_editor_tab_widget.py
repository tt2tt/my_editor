from __future__ import annotations

from pathlib import Path
from typing import Generator, cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QPlainTextEdit

from views.editor_tab_widget import EditorTabWidget


@pytest.fixture(name="qt_app")
def fixture_qt_app() -> Generator[QApplication, None, None]:
    """テスト全体で共有するQApplicationインスタンスを保持する。"""
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    app = cast(QApplication, app_instance)
    yield app


@pytest.fixture(name="tab_widget")
def fixture_tab_widget(qt_app: QApplication) -> Generator[EditorTabWidget, None, None]:
    """EditorTabWidgetを生成しテスト後に破棄する。"""
    widget = EditorTabWidget()
    yield widget
    widget.close()
    widget.deleteLater()


def test_add_editor_tab_creates_plain_text(tab_widget: EditorTabWidget) -> None:
    """add_editor_tabがエディタタブを生成することを検証する。"""
    file_path = Path("dummy.py")
    index = tab_widget.add_editor_tab(file_path, "print('hello')")

    assert tab_widget.count() == 1
    assert tab_widget.tabText(index) == "dummy.py"
    editor = tab_widget.widget(index)
    assert isinstance(editor, QPlainTextEdit)
    assert editor.toPlainText() == "print('hello')"


def test_set_dirty_marks_tab(tab_widget: EditorTabWidget) -> None:
    """set_dirtyでタブタイトルと状態が更新されることを検証する。"""
    index = tab_widget.add_editor_tab(Path("example.txt"), "example")

    tab_widget.set_dirty(index, True)
    assert tab_widget.tabText(index).endswith("*")
    editor = tab_widget.widget(index)
    assert isinstance(editor, QPlainTextEdit)
    assert editor.document().isModified() is True

    tab_widget.set_dirty(index, False)
    assert tab_widget.tabText(index) == "example.txt"
    assert editor.document().isModified() is False


def test_get_current_editor_returns_widget(tab_widget: EditorTabWidget) -> None:
    """get_current_editorがアクティブなエディタを返すことを検証する。"""
    tab_widget.add_editor_tab(Path("sample.md"), "content")
    editor = tab_widget.get_current_editor()
    assert isinstance(editor, QPlainTextEdit)
