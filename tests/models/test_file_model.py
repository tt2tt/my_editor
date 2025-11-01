from __future__ import annotations

import logging
from pathlib import Path

import pytest

from exceptions import FileOperationError
from models.file_model import FileModel


def _cleanup_logger_handlers(logger_name: str) -> None:
    """テスト間の干渉を避けるためロガーハンドラを除去する。"""
    logger = logging.getLogger(logger_name)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_load_and_save(tmp_path: Path) -> None:
    """ファイルの読み込みと保存が行えることを確認する。"""
    # テスト用ファイルとロガーを準備する。
    source_file = tmp_path / "sample.txt"
    source_file.write_text("hello world", encoding="utf-8")
    logger = logging.getLogger("my_editor.test.file_model")

    # モデルでファイルを読み込み、内容とオープンファイル一覧を検証する。
    model = FileModel(logger=logger)
    content = model.load_file(source_file)
    assert content == "hello world"

    # 保存処理を実行し、書き込まれた内容と追跡状態を確認する。
    target_file = tmp_path / "output.txt"
    model.save_file(target_file, "new content")
    assert target_file.read_text(encoding="utf-8") == "new content"

    open_files = set(model.list_open_files())
    assert source_file.resolve() in open_files
    assert target_file.resolve() in open_files

    # 後続テストへの影響を避けるためロガーをクリーンアップする。
    _cleanup_logger_handlers("my_editor.test.file_model")


def test_load_file_missing_raises(tmp_path: Path) -> None:
    """存在しないファイルを読み込むと例外が発生することを確認する。"""
    model = FileModel()

    with pytest.raises(FileOperationError):
        model.load_file(tmp_path / "missing.txt")


def test_load_file_fallback_encoding(tmp_path: Path) -> None:
    """UTF-16などのファイルでもフォールバックにより読み込めることを確認する。"""
    target = tmp_path / "utf16.txt"
    target.write_text("fallback text", encoding="utf-16")

    model = FileModel()
    content = model.load_file(target)

    assert content == "fallback text"
    assert target.resolve() in set(model.list_open_files())
