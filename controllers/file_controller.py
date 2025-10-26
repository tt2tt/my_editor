from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QPlainTextEdit

from models.file_model import FileModel
from models.tab_model import TabState
from views.editor_tab_widget import EditorTabWidget


class FileController:
    """ファイル操作とエディタタブの連携を担うコントローラ。"""

    def __init__(
        self,
        file_model: FileModel,
        tab_state: TabState,
        tab_view: EditorTabWidget,
        *,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """必要な依存を受け取り内部状態を初期化する。

        Args:
            file_model (FileModel): ファイルの読み書きを担当するモデル。
            tab_state (TabState): タブの状態管理を行うモデル。
            tab_view (EditorTabWidget): エディタタブのビュー。
            logger (Optional[logging.Logger]): ログ出力に使用するロガー。
        """
        self._file_model = file_model
        self._tab_state = tab_state
        self._tab_view = tab_view
        self._logger = logger or logging.getLogger("my_editor.file_controller")

        # エディタウィジェットとタブIDの対応関係を追跡する。
        self._tab_id_by_editor: dict[QPlainTextEdit, str] = {}

    def open_file(self, path: Path) -> int:
        """ファイルを開き、エディタタブに内容を表示する。

        Args:
            path (Path): 開くファイルのパス。

        Returns:
            int: 追加されたタブのインデックス。
        """
        self._logger.info("ファイルを開きます: %s", path)
        content = self._file_model.load_file(path)

        tab_id = self._tab_state.add_tab(path)
        tab_index = self._tab_view.add_editor_tab(path, content)

        editor_widget = self._tab_view.widget(tab_index)
        if not isinstance(editor_widget, QPlainTextEdit):
            self._logger.error("エディタウィジェットの生成に失敗しました: index=%s", tab_index)
            raise RuntimeError("エディタウィジェットの生成に失敗しました。")

        self._tab_id_by_editor[editor_widget] = tab_id
        editor_widget.textChanged.connect(lambda editor=editor_widget: self.on_editor_text_changed(editor))
        self._tab_view.setCurrentIndex(tab_index)
        return tab_index

    def save_current_file(self) -> Optional[Path]:
        """アクティブなタブの内容を現在のパスへ保存する。

        Returns:
            Optional[Path]: 保存に利用したファイルパス。保存対象が無い場合はNone。
        """
        editor = self._extract_current_editor()
        if editor is None:
            return None

        tab_id = self._require_tab_id(editor)
        target_path = self._tab_state.get_file_path(tab_id)
        self._logger.info("ファイルを保存します: %s", target_path)

        self._file_model.save_file(target_path, editor.toPlainText())
        self._tab_state.mark_dirty(tab_id, False)

        tab_index = self._tab_view.indexOf(editor)
        if tab_index != -1:
            self._tab_view.set_dirty(tab_index, False)

        return target_path

    def save_file_as(self, path: Path) -> Optional[Path]:
        """アクティブなタブの内容を別名で保存する。

        Args:
            path (Path): 保存先のファイルパス。

        Returns:
            Optional[Path]: 保存に利用したファイルパス。保存対象が無い場合はNone。
        """
        editor = self._extract_current_editor()
        if editor is None:
            return None

        tab_id = self._require_tab_id(editor)
        resolved = path.expanduser().resolve(strict=False)
        self._logger.info("別名でファイルを保存します: %s", resolved)

        self._file_model.save_file(resolved, editor.toPlainText())
        self._tab_state.update_path(tab_id, resolved)
        self._tab_state.mark_dirty(tab_id, False)

        tab_index = self._tab_view.indexOf(editor)
        if tab_index != -1:
            self._tab_view.update_tab_path(tab_index, resolved)
            self._tab_view.set_dirty(tab_index, False)

        return resolved

    def _extract_current_editor(self) -> Optional[QPlainTextEdit]:
        """現在アクティブなエディタを取得する。"""
        editor = self._tab_view.get_current_editor()
        if editor is None:
            self._logger.warning("アクティブなエディタが存在しないため保存を中止しました。")
        return editor

    def on_editor_text_changed(self, editor: Optional[QPlainTextEdit] = None) -> None:
        """エディタ内容の変更を検知してダーティ状態を更新する。"""
        target = editor or self._tab_view.get_current_editor()
        if target is None:
            self._logger.debug("テキスト変更を処理できません。エディタが未選択です。")
            return

        try:
            tab_id = self._require_tab_id(target)
        except KeyError:
            self._logger.warning("テキスト変更の発生元タブを特定できませんでした。")
            return

        if self._tab_state.is_dirty(tab_id):
            return

        self._tab_state.mark_dirty(tab_id, True)

        tab_index = self._tab_view.indexOf(target)
        if tab_index != -1:
            self._tab_view.set_dirty(tab_index, True)

        self._logger.info("タブをダーティ状態へ更新しました: id=%s", tab_id)

    def _require_tab_id(self, editor: QPlainTextEdit) -> str:
        """エディタに紐づくタブIDを取得する。存在しない場合は例外を送出する。"""
        try:
            return self._tab_id_by_editor[editor]
        except KeyError as exc:
            self._logger.error("タブIDの特定に失敗しました。", exc_info=exc)
            raise KeyError("タブIDが関連付けられていません。") from exc
