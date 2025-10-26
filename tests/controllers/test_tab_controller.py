from __future__ import annotations

from pathlib import Path
from typing import Generator, cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QPlainTextEdit

from controllers.tab_controller import TabController
from models.tab_model import TabState
from views.editor_tab_widget import EditorTabWidget


@pytest.fixture(name="qt_app")
def fixture_qt_app() -> Generator[QApplication, None, None]:
    """テスト全体で共有するQApplicationインスタンスを準備する。"""
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    app = cast(QApplication, app_instance)
    yield app


def test_create_tab_initializes_view(qt_app: QApplication, tmp_path: Path) -> None:
    """create_tabでモデルとビューの両方が更新されることを検証する。"""
    state = TabState()
    view = EditorTabWidget()
    controller = TabController(state, view)

    file_path = tmp_path / "example.txt"
    tab_id = controller.create_tab(file_path, "content")

    assert state.get_file_path(tab_id) == file_path.resolve()
    assert view.count() == 1
    editor = view.get_current_editor()
    assert isinstance(editor, QPlainTextEdit)
    assert editor.toPlainText() == "content"
    assert view.tabText(0) == file_path.name


def test_mark_current_dirty_updates_state(qt_app: QApplication, tmp_path: Path) -> None:
    """mark_current_dirtyで状態とタブ表示が同期して更新されることを検証する。"""
    state = TabState()
    view = EditorTabWidget()
    controller = TabController(state, view)

    file_path = tmp_path / "dirty.txt"
    tab_id = controller.create_tab(file_path, "data")

    editor = view.get_current_editor()
    assert editor is not None
    controller.mark_current_dirty(True)

    assert state.is_dirty(tab_id) is True
    assert view.tabText(0).endswith("*")

    controller.mark_current_dirty(False)
    assert state.is_dirty(tab_id) is False
    assert view.tabText(0) == file_path.name


def test_close_tab_removes_view_and_state(qt_app: QApplication, tmp_path: Path) -> None:
    """close_tabでビューとモデルからタブが取り除かれることを検証する。"""
    state = TabState()
    view = EditorTabWidget()
    controller = TabController(state, view)

    first = controller.create_tab(tmp_path / "first.txt", "1")
    second = controller.create_tab(tmp_path / "second.txt", "2")

    controller.close_tab(first)

    assert view.count() == 1
    remaining_editor = view.get_current_editor()
    assert remaining_editor is not None
    assert state.get_file_path(second) == (tmp_path / "second.txt").resolve()
    with pytest.raises(KeyError):
        state.get_file_path(first)