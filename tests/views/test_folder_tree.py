from __future__ import annotations

from pathlib import Path
from typing import Generator, Iterable, cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from views.folder_tree import FolderNode, FolderTree


@pytest.fixture(name="qt_app")
def fixture_qt_app() -> Generator[QApplication, None, None]:
    """テスト全体で共有するQApplicationインスタンスを保持する。"""
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    app = cast(QApplication, app_instance)
    yield app


def _build_nodes(base: Path) -> Iterable[FolderNode]:
    """テスト用の単純なフォルダ階層を生成する。"""
    return [
        FolderNode(
            name="src",
            path=base / "src",
            is_directory=True,
            children=[
                FolderNode(name="main.py", path=base / "src" / "main.py", is_directory=False),
                FolderNode(name="utils", path=base / "src" / "utils", is_directory=True),
            ],
        ),
        FolderNode(name="README.md", path=base / "README.md", is_directory=False),
    ]


def test_populate_sets_items(qt_app: QApplication, tmp_path: Path) -> None:
    """populateが階層構造をツリーに反映することを検証する。"""
    tree = FolderTree()
    nodes = _build_nodes(tmp_path)

    tree.populate(nodes)

    assert tree.topLevelItemCount() == 2
    src_item = tree.topLevelItem(0)
    assert src_item is not None
    assert src_item.text(0) == "src"
    assert src_item.childCount() == 2

    readme_item = tree.topLevelItem(1)
    assert readme_item is not None
    assert readme_item.text(0) == "README.md"


def test_select_path_marks_item(qt_app: QApplication, tmp_path: Path) -> None:
    """select_pathで指定アイテムが選択されることを検証する。"""
    tree = FolderTree()
    nodes = _build_nodes(tmp_path)
    tree.populate(nodes)

    target_path = tmp_path / "src" / "main.py"
    tree.select_path(target_path)

    current = tree.currentItem()
    assert current is not None
    assert current.text(0) == "main.py"


def test_select_path_missing_raises(qt_app: QApplication, tmp_path: Path) -> None:
    """select_pathで存在しないパスを指定すると例外が発生することを検証する。"""
    tree = FolderTree()
    tree.populate([])

    with pytest.raises(Exception):
        tree.select_path(tmp_path / "missing")
