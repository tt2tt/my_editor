from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path
from typing import Iterable


class ProgressUpdater:
    """進捗ファイルを更新する責務を持つクラス。"""

    def __init__(self, progress_path: Path) -> None:
        self._progress_path = progress_path

    def mark_complete(self, item_number: int, *, completed_date: _dt.date | None = None) -> None:
        """指定された項目番号に完了マークと日付を付与する。"""
        if item_number <= 0:
            raise ValueError("項目番号は1以上を指定してください。")

        if not self._progress_path.exists():
            raise FileNotFoundError(f"進捗ファイルが見つかりません: {self._progress_path}")

        lines = self._progress_path.read_text(encoding="utf-8").splitlines()
        updated = False
        completed_on = completed_date or _dt.date.today()
        marker = completed_on.strftime("%Y-%m-%d")

        for index, original in enumerate(lines):
            stripped = original.lstrip()
            prefix = f"{item_number}. "
            if not stripped.startswith(prefix):
                continue

            body = stripped[len(prefix) :].strip()
            if " 〇" in body:
                task_label = body.split(" 〇", 1)[0].strip()
            else:
                task_label = body
            task_label = task_label.replace("✕", "").strip()
            lines[index] = f"{item_number}. {task_label} 〇 {marker} 完了"
            updated = True
            break

        if not updated:
            raise ValueError(f"指定した項目番号が進捗ファイルに存在しません: {item_number}")

        self._progress_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def mark_multiple(self, item_numbers: Iterable[int], *, completed_date: _dt.date | None = None) -> None:
        """複数の項目番号をまとめて完了にする。"""
        for number in item_numbers:
            self.mark_complete(number, completed_date=completed_date)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(description="進捗ファイルの完了項目を更新します。")
    parser.add_argument("item", type=int, nargs="+", help="完了にする項目番号")
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        default=Path("document/progress.txt"),
        help="進捗ファイルのパス",
    )
    parser.add_argument(
        "--date",
        "-d",
        type=str,
        help="完了日 (YYYY-MM-DD)。省略時は本日の日付を使用",
    )
    return parser.parse_args(argv)


def _parse_date(value: str | None) -> _dt.date | None:
    """文字列を日付へ変換する補助関数。"""
    if value is None:
        return None
    try:
        return _dt.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("日付は YYYY-MM-DD 形式で指定してください。") from exc


def main(argv: list[str] | None = None) -> int:
    """エントリーポイント。"""
    args = _parse_args(argv)
    completed_date = _parse_date(args.date)
    updater = ProgressUpdater(args.file)
    updater.mark_multiple(args.item, completed_date=completed_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
