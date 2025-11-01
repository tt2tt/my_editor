from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TabEntry:
    """タブに紐づく情報を保持するデータ構造。"""

    file_path: Path
    is_dirty: bool = False


class TabState:
    """タブの開閉やダーティ状態を管理するモデル。"""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """ロガーを注入し内部状態を初期化する。"""
        # 操作用ロガーとタブ情報の辞書を保持する。
        self._logger = logger or logging.getLogger("my_editor.tab_state")
        self._tabs: dict[str, TabEntry] = {}

    def add_tab(self, file_path: Path) -> str:
        """タブを追加し、その識別子を返す。"""
        normalized_path = file_path.expanduser()
        resolved_path = normalized_path.resolve(strict=False)

        tab_id = uuid.uuid4().hex
        self._tabs[tab_id] = TabEntry(file_path=resolved_path)
        self._logger.info("タブを追加しました: id=%s path=%s", tab_id, resolved_path)
        return tab_id

    def mark_dirty(self, tab_id: str, dirty: bool) -> None:
        """タブのダーティ状態を更新する。"""
        entry = self._get_entry(tab_id)
        entry.is_dirty = dirty
        self._logger.info("タブの状態を更新しました: id=%s dirty=%s", tab_id, dirty)

    def close_tab(self, tab_id: str) -> None:
        """タブを閉じて状態管理から除外する。"""
        if tab_id not in self._tabs:
            self._logger.error("存在しないタブIDが指定されました: %s", tab_id)
            raise KeyError(f"存在しないタブIDです: {tab_id}")

        del self._tabs[tab_id]
        self._logger.info("タブをクローズしました: id=%s", tab_id)

    def is_dirty(self, tab_id: str) -> bool:
        """タブがダーティかどうかを取得する。"""
        return self._get_entry(tab_id).is_dirty

    def get_file_path(self, tab_id: str) -> Path:
        """タブに紐づくファイルパスを取得する。"""
        return self._get_entry(tab_id).file_path

    def update_path(self, tab_id: str, new_path: Path) -> None:
        """タブに紐づくファイルパスを更新する。"""
        entry = self._get_entry(tab_id)
        resolved = new_path.expanduser().resolve(strict=False)
        entry.file_path = resolved
        self._logger.info("タブのパスを更新しました: id=%s path=%s", tab_id, resolved)

    def find_tab_id_by_path(self, path: Path) -> Optional[str]:
        """ファイルパスに一致するタブIDを検索する。"""
        resolved = path.expanduser().resolve(strict=False)
        for tab_id, entry in self._tabs.items():
            if entry.file_path == resolved:
                return tab_id
        return None

    def _get_entry(self, tab_id: str) -> TabEntry:
        """内部で利用するタブ情報取得ヘルパー。"""
        try:
            return self._tabs[tab_id]
        except KeyError as exc:
            self._logger.error("存在しないタブIDが指定されました: %s", tab_id)
            raise KeyError(f"存在しないタブIDです: {tab_id}") from exc
