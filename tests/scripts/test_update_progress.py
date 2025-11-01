from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest

from scripts.update_progress import ProgressUpdater


def test_mark_complete_updates_target_line(tmp_path: Path) -> None:
    content = (
        "フェーズ8\n"
        "31. テストタスク ✕\n"
        "32. 別タスク ✕\n"
    )
    progress_file = tmp_path / "progress.txt"
    progress_file.write_text(content, encoding="utf-8")

    updater = ProgressUpdater(progress_file)
    updater.mark_complete(31, completed_date=_dt.date(2025, 11, 1))

    updated = progress_file.read_text(encoding="utf-8")
    assert "31. テストタスク 〇 2025-11-01 完了" in updated


def test_mark_complete_raises_when_item_missing(tmp_path: Path) -> None:
    progress_file = tmp_path / "progress.txt"
    progress_file.write_text("1. 例 ✕\n", encoding="utf-8")

    updater = ProgressUpdater(progress_file)

    with pytest.raises(ValueError):
        updater.mark_complete(99, completed_date=_dt.date(2025, 11, 1))


def test_mark_multiple_updates_each(tmp_path: Path) -> None:
    content = (
        "31. タスクA ✕\n"
        "32. タスクB ✕\n"
        "33. タスクC ✕\n"
    )
    progress_file = tmp_path / "progress.txt"
    progress_file.write_text(content, encoding="utf-8")

    updater = ProgressUpdater(progress_file)
    updater.mark_multiple([31, 33], completed_date=_dt.date(2025, 11, 1))

    updated = progress_file.read_text(encoding="utf-8")
    assert "31. タスクA 〇 2025-11-01 完了" in updated
    assert "33. タスクC 〇 2025-11-01 完了" in updated
    assert "32. タスクB ✕" in updated
