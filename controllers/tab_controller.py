from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QPlainTextEdit

from models.tab_model import TabState
from views.editor_tab_widget import EditorTabWidget


class TabController:
    """タブ状態モデルとエディタビューを連携させるコントローラ。"""

    def __init__(
        self,
        tab_state: TabState,
        tab_view: EditorTabWidget,
        *,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """依存関係を受け取り内部状態を初期化する。"""
        self._tab_state = tab_state
        self._tab_view = tab_view
        self._logger = logger or logging.getLogger("my_editor.tab_controller")
        self._tab_id_by_editor: dict[QPlainTextEdit, str] = {}

    def create_tab(self, path: Path, content: str) -> str:
        """新しいエディタタブを作成してタブIDを返す。"""
        tab_id = self._tab_state.add_tab(path)
        index = self._tab_view.add_editor_tab(path, content)
        self._tab_view.setCurrentIndex(index)
        self._tab_view.set_dirty(index, False)
        editor = self._tab_view.widget(index)
        if isinstance(editor, QPlainTextEdit):
            self._tab_id_by_editor[editor] = tab_id
        self._logger.info("タブを生成しました: id=%s index=%s", tab_id, index)
        return tab_id

    def mark_current_dirty(self, status: bool) -> None:
        """現在のタブのダーティ状態を更新する。"""
        editor = self._get_current_editor()
        if editor is None:
            self._logger.warning("ダーティ状態を更新できません。アクティブなタブが存在しません。")
            return

        index = self._tab_view.indexOf(editor)
        if index == -1:
            self._logger.error("アクティブなエディタのタブインデックスを特定できません。")
            raise RuntimeError("タブインデックスを特定できません。")

        tab_id = self._resolve_tab_id(editor)
        self._tab_state.mark_dirty(tab_id, status)
        self._tab_view.set_dirty(index, status)
        self._logger.info("タブのダーティ状態を更新しました: id=%s dirty=%s", tab_id, status)

    def close_tab(self, tab_id: str) -> None:
        """指定されたタブを閉じ、ビュー上でも除去する。"""
        for index in range(self._tab_view.count()):
            widget = self._tab_view.widget(index)
            if not isinstance(widget, QPlainTextEdit):
                continue
            if self._resolve_tab_id(widget) == tab_id:
                self._tab_id_by_editor.pop(widget, None)
                self._tab_view.removeTab(index)
                break
        else:
            self._logger.error("指定されたタブIDがビュー内に見つかりません: %s", tab_id)
            raise KeyError(f"タブIDが存在しません: {tab_id}")

        self._tab_state.close_tab(tab_id)
        self._logger.info("タブを閉じました: id=%s", tab_id)

    def _get_current_editor(self) -> Optional[QPlainTextEdit]:
        """現在アクティブなエディタウィジェットを取得する。"""
        editor = self._tab_view.get_current_editor()
        return editor

    def _resolve_tab_id(self, editor: QPlainTextEdit) -> str:
        """エディタウィジェットからタブIDを推定する。"""
        if editor not in self._tab_id_by_editor:
            self._logger.error("タブIDがマッピングされていません。")
            raise KeyError("タブIDがマッピングされていません。")
        return self._tab_id_by_editor[editor]
