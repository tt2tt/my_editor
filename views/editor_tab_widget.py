from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtWidgets import QTabWidget, QWidget

from views.editor_widget import EditorWidget


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
        # タブクローズ要求を委譲するハンドラを保持する。
        self._close_request_handler: Callable[[int], None] | None = None

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._handle_tab_close_requested)

    def add_editor_tab(self, file_path: Path, content: str) -> int:
        """ファイル内容を表示するタブを追加する。"""
        # エディタウィジェットを生成して内容を読み込む。
        editor = EditorWidget(self)
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

    def close_tab(self, tab_index: int) -> Optional[Path]:
        """指定インデックスのタブを閉じる。"""
        metadata, widget = self._get_metadata(tab_index)
        removed_path = metadata.path

        self._metadata_map.pop(widget, None)
        self.removeTab(tab_index)
        widget.deleteLater()
        self._logger.info("エディタタブを閉じました: index=%s, path=%s", tab_index, removed_path)
        return removed_path

    def close_current_tab(self) -> Optional[Path]:
        """現在アクティブなタブを閉じる。"""
        current_index = self.currentIndex()
        if current_index == -1:
            return None
        return self.close_tab(current_index)

    def set_close_request_handler(self, handler: Callable[[int], None]) -> None:
        """タブクローズ要求を処理するハンドラを設定する。"""
        self._close_request_handler = handler

    def set_dirty(self, tab_index: int, dirty: bool) -> None:
        """タブのダーティ状態を更新する。"""
        metadata, editor = self._get_metadata(tab_index)

        # 表示名を更新して変更状態を示す。
        display_title = f"{metadata.title}*" if dirty else metadata.title
        self.setTabText(tab_index, display_title)

        if isinstance(editor, EditorWidget):
            editor.document().setModified(dirty)

        metadata.is_dirty = dirty
        self._logger.info("タブの状態を更新しました: index=%s dirty=%s", tab_index, dirty)

    def update_tab_path(self, tab_index: int, new_path: Path) -> None:
        """タブに紐づくパス情報を更新する。"""
        metadata, _ = self._get_metadata(tab_index)
        resolved = new_path.expanduser().resolve(strict=False)
        metadata.path = resolved
        metadata.title = resolved.name or str(resolved)

        display_title = f"{metadata.title}*" if metadata.is_dirty else metadata.title
        self.setTabText(tab_index, display_title)
        self.setTabToolTip(tab_index, str(resolved))
        self._logger.info("タブのパスを更新しました: index=%s path=%s", tab_index, resolved)

    def get_current_editor(self) -> Optional[EditorWidget]:
        """現在アクティブなエディタウィジェットを返す。"""
        widget = self.currentWidget()
        if isinstance(widget, EditorWidget):
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

    def _handle_tab_close_requested(self, index: int) -> None:
        """Qtシグナルからのクローズ要求を仲介する。"""
        if self._close_request_handler is not None:
            self._close_request_handler(index)
            return

        # ハンドラ未設定の場合はビュー側で処理する。
        try:
            self.close_tab(index)
        except (IndexError, KeyError):
            self._logger.debug("クローズ対象タブの特定に失敗しました: index=%s", index)
