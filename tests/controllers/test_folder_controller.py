from __future__ import annotations

from pathlib import Path
from typing import Generator, cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QTreeWidgetItem

from controllers.folder_controller import FolderController
from exceptions import FileOperationError
from models.folder_model import FolderModel
from views.folder_tree import FolderTree


@pytest.fixture(name="qt_app")
def fixture_qt_app() -> Generator[QApplication, None, None]:
    """テスト全体で共有するQApplicationインスタンスを準備する。"""
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    app = cast(QApplication, app_instance)
    yield app


def _collect_child_names(item: QTreeWidgetItem) -> set[str]:
    """指定アイテム直下の子要素名を集合で取得する。"""
    return {item.child(index).text(0) for index in range(item.childCount())}


def test_load_initial_tree_populates_view(qt_app: QApplication, tmp_path: Path) -> None:
    """load_initial_treeでルート配下の構造がツリーに反映されることを検証する。"""
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('ok')", encoding="utf-8")
    (root / "README.md").write_text("# title", encoding="utf-8")

    tree = FolderTree()
    controller = FolderController(FolderModel(), tree)

    controller.load_initial_tree(root)

    assert tree.topLevelItemCount() == 1
    root_item = tree.topLevelItem(0)
    assert root_item is not None
    assert root_item.text(0) == "workspace"
    child_names = _collect_child_names(root_item)
    assert {"src", "README.md"} <= child_names

    src_item = next(
        (root_item.child(i) for i in range(root_item.childCount()) if root_item.child(i).text(0) == "src"),
        None,
    )
    assert src_item is not None
    assert _collect_child_names(src_item) == {"main.py"}


def test_handle_create(qt_app: QApplication, tmp_path: Path) -> None:
    """handle_createで新規項目が作成されツリーへ反映されることを検証する。"""
    root = tmp_path / "workspace"
    root.mkdir()

    tree = FolderTree()
    controller = FolderController(FolderModel(), tree)
    controller.load_initial_tree(root)

    new_dir = root / "new_dir"
    controller.handle_create(new_dir, is_dir=True)

    assert new_dir.exists()
    assert tree.current_path() == new_dir.resolve()

    root_item = tree.topLevelItem(0)
    assert root_item is not None
    assert "new_dir" in _collect_child_names(root_item)


def test_handle_delete_removes_entry(qt_app: QApplication, tmp_path: Path) -> None:
    """handle_deleteで項目が削除され、ビューが親ディレクトリへ戻ることを検証する。"""
    root = tmp_path / "workspace"
    root.mkdir()
    target = root / "obsolete.txt"
    target.write_text("remove", encoding="utf-8")

    tree = FolderTree()
    controller = FolderController(FolderModel(), tree)
    controller.load_initial_tree(root)

    controller.handle_delete(target)

    assert not target.exists()
    assert tree.current_path() == root.resolve()
    with pytest.raises(FileOperationError):
        tree.select_path(target)
