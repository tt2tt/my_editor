from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QPlainTextEdit, QTabWidget, QWidget


@dataclass
class TabMetadata:
    """タブに紐づくメタ情報。"""

    title: str
    path: Path
    is_dirty: bool = False


class EditorTabWidget(QTabWidget):
    """エディタ用のタブウィジェット。"""

    def __init__(self, parent: Optional[QWidget] = None, *, logger: Optional[logging.Logger] = None) -> None:
        """タブウィジェットを初期化する。"""
        super().__init__(parent)
        # 操作用ロガーを保持する。
        self._logger = logger or logging.getLogger("my_editor.editor_tab_widget")
        # タブとメタ情報の紐づけを追跡する。
        self._metadata_map: dict[QWidget, TabMetadata] = {}

    def add_editor_tab(self, file_path: Path, content: str) -> int:
        """ファイル内容を表示するタブを追加する。"""
        # エディタウィジェットを生成して内容を読み込む。
        editor = QPlainTextEdit(self)
        editor.setPlainText(content)
        editor.document().setModified(False)

        # ファイル名をタブタイトルに設定して追加する。
        title = file_path.name or str(file_path)
        index = self.addTab(editor, title)
        self.setTabToolTip(index, str(file_path))

        # メタ情報を保持して追跡する。
        metadata = TabMetadata(title=title, path=file_path)
        self._metadata_map[editor] = metadata
        self._logger.info("エディタタブを追加しました: index=%s, path=%s", index, file_path)
        return index

    def set_dirty(self, tab_index: int, dirty: bool) -> None:
        """タブのダーティ状態を更新する。"""
        metadata, editor = self._get_metadata(tab_index)

        # 表示名を更新して変更状態を示す。
        display_title = f"{metadata.title}*" if dirty else metadata.title
        self.setTabText(tab_index, display_title)

        if isinstance(editor, QPlainTextEdit):
            editor.document().setModified(dirty)

        metadata.is_dirty = dirty
        self._logger.info("タブの状態を更新しました: index=%s dirty=%s", tab_index, dirty)

    def get_current_editor(self) -> Optional[QPlainTextEdit]:
        """現在アクティブなエディタウィジェットを返す。"""
        widget = self.currentWidget()
        if isinstance(widget, QPlainTextEdit):
            return widget
        return None

    def _get_metadata(self, tab_index: int) -> tuple[TabMetadata, QWidget]:
        """タブに設定されたメタ情報とウィジェットを取得する。"""
        if not 0 <= tab_index < self.count():
            raise IndexError(f"タブインデックスが範囲外です: {tab_index}")

        widget = self.widget(tab_index)
        if widget not in self._metadata_map:
            raise KeyError(f"タブメタデータが存在しません: {tab_index}")
        return self._metadata_map[widget], widget
