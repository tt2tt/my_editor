from __future__ import annotations

from pathlib import Path
from typing import Generator, cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint
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


def test_load_initial_tree_sorts_directories_first(qt_app: QApplication, tmp_path: Path) -> None:
    """ディレクトリがファイルより上に表示される順序を検証する。"""
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "docs").mkdir()
    (root / "src").mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    (root / "b.txt").write_text("b", encoding="utf-8")

    tree = FolderTree()
    controller = FolderController(FolderModel(), tree)

    controller.load_initial_tree(root)

    root_item = tree.topLevelItem(0)
    assert root_item is not None
    child_order = [root_item.child(index).text(0) for index in range(root_item.childCount())]
    assert child_order == ["docs", "src", "a.txt", "b.txt"]


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


def test_apply_context_action(qt_app: QApplication, tmp_path: Path) -> None:
    """コンテキスト操作がモデル更新とビュー反映に繋がることを検証する。"""
    root = tmp_path / "workspace"
    root.mkdir()
    existing = root / "keep.txt"
    existing.write_text("data", encoding="utf-8")

    tree = FolderTree()
    controller = FolderController(FolderModel(), tree)
    controller.load_initial_tree(root)

    created_file = controller._apply_context_action("create_file", root)
    assert created_file is not None
    assert created_file.exists()
    assert tree.current_path() == created_file.resolve()

    created_folder = controller._apply_context_action("create_folder", root)
    assert created_folder is not None
    assert created_folder.exists()
    assert created_folder.is_dir()

    controller._apply_context_action("delete", existing)
    assert not existing.exists()

    captured: list[tuple[str, Path]] = []
    tree.set_context_action_handler(lambda action, path: captured.append((action, path)))
    root_item = tree.topLevelItem(0)
    assert root_item is not None
    tree.setCurrentItem(root_item)
    tree._show_context_menu(QPoint(0, 0), simulate_action="create_file")

    assert captured
    assert captured[0][0] == "create_file"
    assert captured[0][1] == root.resolve()


def test_handle_rename_file_updates_view(qt_app: QApplication, tmp_path: Path) -> None:
    """ファイルの名称変更でファイルシステムとビューが更新されることを検証する。"""
    root = tmp_path / "workspace"
    root.mkdir()
    target = root / "old.txt"
    target.write_text("content", encoding="utf-8")

    tree = FolderTree()
    controller = FolderController(FolderModel(), tree)
    controller.load_initial_tree(root)

    controller._prompt_new_name = lambda _: "renamed.txt"  # type: ignore[assignment]

    result = controller.handle_rename(target)

    assert result == root / "renamed.txt"
    assert result is not None
    assert result.exists()
    assert not target.exists()

    tree.select_path(result)
    current = tree.currentItem()
    assert current is not None
    assert current.text(0) == "renamed.txt"


def test_handle_rename_directory_updates_children(qt_app: QApplication, tmp_path: Path) -> None:
    """フォルダの名称変更で子要素のパスが維持されることを検証する。"""
    root = tmp_path / "workspace"
    root.mkdir()
    source_dir = root / "src"
    source_dir.mkdir()
    child_file = source_dir / "main.py"
    child_file.write_text("print('ok')", encoding="utf-8")

    tree = FolderTree()
    controller = FolderController(FolderModel(), tree)
    controller.load_initial_tree(root)

    controller._prompt_new_name = lambda _: "package"  # type: ignore[assignment]

    result = controller.handle_rename(source_dir)

    expected_dir = root / "package"
    assert result == expected_dir
    assert expected_dir.exists()
    assert not source_dir.exists()
    assert (expected_dir / "main.py").exists()

    tree.select_path(expected_dir / "main.py")
    current = tree.currentItem()
    assert current is not None
    assert current.text(0) == "main.py"
