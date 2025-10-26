from __future__ import annotations

import logging
from pathlib import Path

import pytest

from exceptions import FileOperationError
from models.folder_model import FolderModel


def _cleanup_logger_handlers(logger_name: str) -> None:
    """テスト間の干渉を防ぐためにロガーハンドラを除去する。"""
    logger = logging.getLogger(logger_name)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_list_directory_returns_sorted_entries(tmp_path: Path) -> None:
    """list_directoryがディレクトリ内容をソートして返すことを検証する。"""
    # テスト用のディレクトリ構造を準備する。
    (tmp_path / "b_file.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a_dir").mkdir()
    (tmp_path / "c_file.txt").write_text("c", encoding="utf-8")

    logger = logging.getLogger("my_editor.test.folder_model")
    model = FolderModel(logger=logger)

    # 取得結果が決定的な順序で返ることを確認する。
    entries = model.list_directory(tmp_path)
    expected = sorted(tmp_path.iterdir())
    assert entries == expected

    _cleanup_logger_handlers("my_editor.test.folder_model")


def test_create_item_creates_file_and_directory(tmp_path: Path) -> None:
    """create_itemでファイルとディレクトリを生成できることを検証する。"""
    model = FolderModel()

    file_path = tmp_path / "note.txt"
    dir_path = tmp_path / "docs"

    model.create_item(file_path, is_dir=False)
    model.create_item(dir_path, is_dir=True)

    assert file_path.exists() and file_path.is_file()
    assert dir_path.exists() and dir_path.is_dir()


def test_delete_item_removes_targets(tmp_path: Path) -> None:
    """delete_itemがファイルと空ディレクトリを削除することを検証する。"""
    model = FolderModel()

    file_path = tmp_path / "remove.txt"
    dir_path = tmp_path / "empty"
    file_path.write_text("data", encoding="utf-8")
    dir_path.mkdir()

    model.delete_item(file_path)
    model.delete_item(dir_path)

    assert not file_path.exists()
    assert not dir_path.exists()


def test_delete_item_raises_when_directory_not_empty(tmp_path: Path) -> None:
    """中身のあるディレクトリ削除で例外が発生することを検証する。"""
    model = FolderModel()

    dir_path = tmp_path / "non_empty"
    dir_path.mkdir()
    (dir_path / "child.txt").write_text("x", encoding="utf-8")

    with pytest.raises(FileOperationError):
        model.delete_item(dir_path)


def test_list_directory_missing_path_raises(tmp_path: Path) -> None:
    """存在しないディレクトリを列挙しようとすると例外が発生することを検証する。"""
    model = FolderModel()

    with pytest.raises(FileOperationError):
        model.list_directory(tmp_path / "missing")
