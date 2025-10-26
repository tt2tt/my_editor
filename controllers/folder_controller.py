from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Optional

from exceptions import FileOperationError
from models.folder_model import FolderModel
from views.folder_tree import FolderNode, FolderTree


class FolderController:
    """フォルダモデルとビューを調停するコントローラ。"""

    def __init__(
        self,
        folder_model: FolderModel,
        folder_view: FolderTree,
        *,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """依存関係を受け取りコントローラを初期化する。"""
        self._folder_model = folder_model
        self._folder_view = folder_view
        self._logger = logger or logging.getLogger("my_editor.folder_controller")
        self._current_root: Optional[Path] = None

    def load_initial_tree(self, path: Path) -> None:
        """ルートディレクトリを読み込みツリービューを構築する。"""
        resolved = self._normalize(path)
        if not resolved.exists():
            self._logger.error("ルートディレクトリが存在しません: %s", resolved)
            raise FileOperationError(f"ルートディレクトリが存在しません: {resolved}")
        if not resolved.is_dir():
            self._logger.error("ルートがディレクトリではありません: %s", resolved)
            raise FileOperationError(f"ルートがディレクトリではありません: {resolved}")

        self._current_root = resolved
        root_node = self._build_node(resolved)
        self._folder_view.populate([root_node])
        self._attempt_select(resolved)
        self._logger.info("フォルダツリーを初期化しました: %s", resolved)

    def handle_create(self, path: Path, is_dir: bool) -> None:
        """新しいファイルまたはディレクトリを作成しツリーを更新する。"""
        self._require_root()
        target = self._normalize(path)
        self._logger.info("項目の作成を開始します: %s", target)

        self._folder_model.create_item(target, is_dir=is_dir)
        self._reload_tree(select_path=target)
        self._logger.info("項目を作成しツリーを更新しました: %s", target)

    def handle_delete(self, path: Path) -> None:
        """ファイルまたはディレクトリを削除しツリーを最新化する。"""
        root = self._require_root()
        target = self._normalize(path)
        self._logger.info("項目の削除を開始します: %s", target)

        self._folder_model.delete_item(target)
        parent = target.parent if target != root else root
        if not parent.exists() or not self._is_under_root(parent):
            parent = root

        self._reload_tree(select_path=parent)
        self._logger.info("項目を削除しツリーを更新しました: %s", target)

    def _reload_tree(self, select_path: Optional[Path]) -> None:
        """現在のルートからツリーを再構築する。"""
        root = self._require_root()
        root_node = self._build_node(root)
        self._folder_view.populate([root_node])

        candidates: list[Path] = []
        if select_path is not None:
            candidates.append(select_path)
        candidates.append(root)

        for candidate in candidates:
            if not candidate.exists():
                continue
            self._attempt_select(candidate)
            current = self._folder_view.current_path()
            if current is None:
                continue
            if self._normalize(current) == self._normalize(candidate):
                break

    def _build_node(self, path: Path) -> FolderNode:
        """指定パスを起点にフォルダノードを再帰的に生成する。"""
        resolved = self._normalize(path)
        is_directory = resolved.is_dir()
        children: Iterable[FolderNode] | None = None

        if is_directory:
            entries = self._folder_model.list_directory(resolved)
            children = [self._build_node(entry) for entry in entries]

        name = resolved.name or str(resolved)
        return FolderNode(name=name, path=resolved, is_directory=is_directory, children=children)

    def _attempt_select(self, path: Path) -> None:
        """ツリー内のパスを選択し、存在しない場合は警告ログを残す。"""
        try:
            self._folder_view.select_path(path)
        except FileOperationError as exc:
            self._logger.warning("ツリー内の選択に失敗しました: %s", path, exc_info=exc)

    def _require_root(self) -> Path:
        """ルートパスを取得し、未設定の場合は例外を送出する。"""
        if self._current_root is None:
            self._logger.error("ルートディレクトリが設定されていません。")
            raise RuntimeError("ルートディレクトリが設定されていません。")
        return self._current_root

    def _is_under_root(self, path: Path) -> bool:
        """対象パスが現在のルート配下か判定する。"""
        root = self._current_root
        if root is None:
            return False
        candidate = self._normalize(path)
        try:
            return candidate == root or candidate.is_relative_to(root)
        except ValueError:
            return False

    @staticmethod
    def _normalize(path: Path) -> Path:
        """パスを正規化して返す。"""
        return path.expanduser().resolve(strict=False)