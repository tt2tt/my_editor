from __future__ import annotations

import logging
from pathlib import Path

import pytest

from models.tab_model import TabState


def _cleanup_logger_handlers(logger_name: str) -> None:
    """テスト間の干渉を避けるためロガーハンドラを除去する。"""
    logger = logging.getLogger(logger_name)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_add_tab_registers_path(tmp_path: Path) -> None:
    """add_tabが新しいタブIDとファイルパスを登録することを検証する。"""
    target = tmp_path / "example.txt"
    target.write_text("content", encoding="utf-8")

    logger = logging.getLogger("my_editor.test.tab_state")
    state = TabState(logger=logger)

    tab_id = state.add_tab(target)
    assert state.get_file_path(tab_id) == target.resolve()
    assert state.is_dirty(tab_id) is False

    _cleanup_logger_handlers("my_editor.test.tab_state")


def test_mark_dirty_updates_state(tmp_path: Path) -> None:
    """mark_dirtyでダーティ状態が更新されることを検証する。"""
    state = TabState()
    tab_id = state.add_tab(tmp_path / "sample.txt")

    state.mark_dirty(tab_id, True)
    assert state.is_dirty(tab_id) is True

    state.mark_dirty(tab_id, False)
    assert state.is_dirty(tab_id) is False


def test_close_tab_removes_entry(tmp_path: Path) -> None:
    """close_tabでタブが除去されることを検証する。"""
    state = TabState()
    tab_id = state.add_tab(tmp_path / "close.txt")

    state.close_tab(tab_id)
    with pytest.raises(KeyError):
        state.is_dirty(tab_id)


def test_mark_dirty_unknown_tab_raises() -> None:
    """存在しないタブIDを指定すると例外が発生することを検証する。"""
    state = TabState()

    with pytest.raises(KeyError):
        state.mark_dirty("missing", True)
