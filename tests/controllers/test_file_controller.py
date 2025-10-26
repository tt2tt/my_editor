from __future__ import annotations

from pathlib import Path
from typing import Generator, cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QPlainTextEdit

from controllers.file_controller import FileController
from models.file_model import FileModel
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


def test_open_file_updates_tab(qt_app: QApplication, tmp_path: Path) -> None:
    """open_fileがファイル内容をタブに読み込むことを検証する。"""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello", encoding="utf-8")

    model = FileModel()
    state = TabState()
    tab_widget = EditorTabWidget()
    controller = FileController(model, state, tab_widget)

    index = controller.open_file(file_path)

    assert tab_widget.count() == 1
    editor_widget = tab_widget.widget(index)
    assert isinstance(editor_widget, QPlainTextEdit)
    assert editor_widget.toPlainText() == "hello"
    assert file_path.resolve() in model.list_open_files()


def test_save_current_file_writes_changes(qt_app: QApplication, tmp_path: Path) -> None:
    """save_current_fileがエディタの内容を保存することを検証する。"""
    file_path = tmp_path / "document.txt"
    file_path.write_text("initial", encoding="utf-8")

    model = FileModel()
    state = TabState()
    tab_widget = EditorTabWidget()
    controller = FileController(model, state, tab_widget)

    index = controller.open_file(file_path)
    editor = tab_widget.get_current_editor()
    assert editor is not None

    editor.setPlainText("updated")
    tab_id = controller._tab_id_by_editor[editor]  # テスト対象の状態を確認するため内部辞書を参照
    state.mark_dirty(tab_id, True)
    tab_widget.set_dirty(index, True)

    saved_path = controller.save_current_file()

    assert saved_path == file_path.resolve()
    assert file_path.read_text(encoding="utf-8") == "updated"
    assert state.is_dirty(tab_id) is False
    assert tab_widget.tabText(index) == file_path.name


def test_save_file_as_updates_tab_state(qt_app: QApplication, tmp_path: Path) -> None:
    """save_file_asが新しいパスへ保存しタブ情報を更新することを検証する。"""
    original = tmp_path / "original.txt"
    original.write_text("before", encoding="utf-8")
    destination = tmp_path / "renamed.txt"

    model = FileModel()
    state = TabState()
    tab_widget = EditorTabWidget()
    controller = FileController(model, state, tab_widget)

    index = controller.open_file(original)
    editor = tab_widget.get_current_editor()
    assert editor is not None
    editor.setPlainText("after")

    tab_id = controller._tab_id_by_editor[editor]
    saved_path = controller.save_file_as(destination)

    assert saved_path == destination.resolve()
    assert destination.read_text(encoding="utf-8") == "after"
    assert state.get_file_path(tab_id) == destination.resolve()
    assert tab_widget.tabText(index) == destination.name
    assert tab_widget.tabToolTip(index) == str(destination.resolve())