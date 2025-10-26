from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, cast

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QAbstractItemView, QTreeWidget, QTreeWidgetItem, QWidget

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

    def current_path(self) -> Optional[Path]:
        """現在選択されているアイテムのパスを返す。"""
        item = cast(Optional[QTreeWidgetItem], self.currentItem())
        if item is None:
            return None

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, str):
            return Path(data)

        return None
