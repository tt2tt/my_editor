from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional, cast

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QAbstractItemView, QMenu, QTreeWidget, QTreeWidgetItem, QWidget

from exceptions import FileOperationError


@dataclass
class FolderNode:
    """フォルダ構造を表すノード情報。"""

    name: str
    path: Path
    is_directory: bool
    children: Iterable["FolderNode"] | None = None


class FolderTree(QTreeWidget):
    """フォルダ階層を表示するツリービュー。"""

    def __init__(self, parent: Optional[QWidget] = None, *, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(parent)
        self._logger = logger or logging.getLogger("my_editor.folder_tree")
        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setIndentation(18)
        self._path_item_map: dict[Path, QTreeWidgetItem] = {}
        self._context_handler: Callable[[str, Path], Optional[Path]] | None = None

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def populate(self, nodes: Iterable[FolderNode]) -> None:
        """与えられたノード情報からツリーデータを構築する。"""
        self.clear()
        self._path_item_map.clear()

        for node in nodes:
            item = self._create_item(node)
            self.addTopLevelItem(item)

        self.expandToDepth(0)
        self._logger.info("フォルダツリーを更新しました。")

    def select_path(self, path: Path) -> None:
        """指定パスのアイテムを選択状態にする。"""
        normalized = path.expanduser().resolve(strict=False)
        if normalized not in self._path_item_map:
            raise FileOperationError(f"パスがツリー内に存在しません: {normalized}")

        item = self._path_item_map[normalized]
        self.setCurrentItem(item)
        self.scrollToItem(item)

    def _create_item(self, node: FolderNode) -> QTreeWidgetItem:
        """単一ノードからツリーアイテムを生成する。"""
        item = QTreeWidgetItem([node.name])
        icon_name = "folder" if node.is_directory else "text-x-generic"
        item.setIcon(0, QIcon.fromTheme(icon_name))
        item.setData(0, Qt.ItemDataRole.UserRole, str(node.path))

        self._path_item_map[node.path.resolve(strict=False)] = item

        for child in node.children or []:
            item.addChild(self._create_item(child))

        return item

    def set_context_action_handler(self, handler: Callable[[str, Path], Optional[Path]]) -> None:
        """コンテキストメニューの操作時に呼び出すハンドラを登録する。"""
        self._context_handler = handler

    def current_path(self) -> Optional[Path]:
        """現在選択されているアイテムのパスを返す。"""
        item = cast(Optional[QTreeWidgetItem], self.currentItem())
        if item is None:
            return None

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, str):
            return Path(data)

        return None

    def _show_context_menu(self, position: QPoint, *, simulate_action: str | None = None) -> None:
        """右クリック時にコンテキストメニューを表示する。"""
        if self._context_handler is None:
            self._logger.debug("コンテキストメニューのハンドラが未設定です。")
            return

        item = cast(Optional[QTreeWidgetItem], self.itemAt(position))
        if item is None:
            current_item = cast(Optional[QTreeWidgetItem], self.currentItem())
            if current_item is None:
                self._logger.debug("コンテキストメニューを表示できる項目が選択されていません。")
                return
            item = current_item

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(data, str):
            self._logger.debug("アイテムのパス情報を取得できません。")
            return

        target_path = Path(data)

        menu = QMenu(self)
        create_file_action = menu.addAction("新規ファイル")
        create_file_action.setData("create_file")
        create_folder_action = menu.addAction("新規フォルダ")
        create_folder_action.setData("create_folder")
        menu.addSeparator()
        delete_action = menu.addAction("削除")
        delete_action.setData("delete")

        if simulate_action is not None:
            selected_key: object = simulate_action
        else:
            global_pos = self.viewport().mapToGlobal(position)
            selected = cast(Optional[QAction], menu.exec(global_pos))
            if selected is None:
                return
            selected_key = selected.data()

        if not isinstance(selected_key, str):
            self._logger.debug("不明なメニュー項目が選択されました。")
            return

        handler = self._context_handler
        handler(selected_key, target_path)
