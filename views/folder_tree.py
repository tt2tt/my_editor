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
        item.setData(0, Qt.ItemDataRole.UserRole + 1, node.is_directory)

        self._path_item_map[node.path.resolve(strict=False)] = item

        for child in node.children or []:
            item.addChild(self._create_item(child))

        return item

    def add_node(self, parent_path: Path, node: FolderNode) -> None:
        """指定パス配下にノードを追加する。"""
        normalized_parent = parent_path.expanduser().resolve(strict=False)
        parent_item = self._path_item_map.get(normalized_parent)
        if parent_item is None:
            raise FileOperationError(f"親ノードが存在しません: {normalized_parent}")

        new_item = self._create_item(node)
        new_key = self._sort_key(node.is_directory, node.name)

        insert_index = parent_item.childCount()
        for index in range(parent_item.childCount()):
            child = parent_item.child(index)
            child_is_dir = bool(child.data(0, Qt.ItemDataRole.UserRole + 1))
            child_key = self._sort_key(child_is_dir, child.text(0))
            if new_key < child_key:
                insert_index = index
                break

        parent_item.insertChild(insert_index, new_item)

    def remove_path(self, path: Path) -> None:
        """指定パスのノードをツリーから削除する。"""
        normalized = path.expanduser().resolve(strict=False)
        target_item = self._path_item_map.get(normalized)
        if target_item is None:
            raise FileOperationError(f"削除対象がツリーに存在しません: {normalized}")

        index = self.indexOfTopLevelItem(target_item)
        if index >= 0:
            removed_item = cast(QTreeWidgetItem, self.takeTopLevelItem(index))
            self._remove_item_recursive(removed_item)
            return

        parent_item = target_item.parent()
        if parent_item is None:
            raise FileOperationError(f"親アイテムの取得に失敗しました: {normalized}")

        parent_item.takeChild(parent_item.indexOfChild(target_item))
        self._remove_item_recursive(target_item)

    def _remove_item_recursive(self, item: QTreeWidgetItem) -> None:
        """ノードとその子孫をマップから再帰的に削除する。"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, str):
            normalized = Path(data).expanduser().resolve(strict=False)
            self._path_item_map.pop(normalized, None)

        while item.childCount() > 0:
            child = item.child(0)
            item.takeChild(0)
            self._remove_item_recursive(child)

    @staticmethod
    def _sort_key(is_directory: bool, name: str) -> tuple[int, str]:
        """ディレクトリ優先のソートキーを生成する。"""
        return (0 if is_directory else 1, name.casefold())

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
        rename_action = menu.addAction("名前を変更")
        rename_action.setData("rename")
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
        assert handler is not None
        handler(selected_key, target_path)

    def rename_path(self, old_path: Path, new_path: Path) -> None:
        """既存ノードのパスと表示名を更新する。"""
        normalized_old = old_path.expanduser().resolve(strict=False)
        item = self._path_item_map.get(normalized_old)
        if item is None:
            raise FileOperationError(f"リネーム対象がツリーに存在しません: {normalized_old}")

        normalized_new = new_path.expanduser().resolve(strict=False)
        display_name = normalized_new.name or str(normalized_new)
        item.setText(0, display_name)
        item.setData(0, Qt.ItemDataRole.UserRole, str(normalized_new))
        self._path_item_map.pop(normalized_old, None)
        self._path_item_map[normalized_new] = item

        is_directory = bool(item.data(0, Qt.ItemDataRole.UserRole + 1))
        if is_directory:
            self._update_child_paths(item, normalized_old, normalized_new)

        self._reinsert_sorted(item)

    def _update_child_paths(self, item: QTreeWidgetItem, old_base: Path, new_base: Path) -> None:
        """子要素のパス情報を再帰的に更新する。"""
        for index in range(item.childCount()):
            child = item.child(index)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if not isinstance(data, str):
                continue

            old_child_path = Path(data).expanduser().resolve(strict=False)
            try:
                relative = old_child_path.relative_to(old_base)
            except ValueError:
                continue

            new_child_path = new_base / relative
            child.setData(0, Qt.ItemDataRole.UserRole, str(new_child_path))
            self._path_item_map.pop(old_child_path, None)
            self._path_item_map[new_child_path] = child

            if child.childCount() > 0:
                self._update_child_paths(child, old_child_path, new_child_path)

    def _reinsert_sorted(self, item: QTreeWidgetItem) -> None:
        """リネーム後にノードをソート順へ差し戻す。"""
        parent_item = cast(Optional[QTreeWidgetItem], item.parent())
        if parent_item is None:
            index = self.indexOfTopLevelItem(item)
            if index >= 0:
                taken = self.takeTopLevelItem(index)
                if taken is not None:
                    item = taken
            self._insert_sorted(None, item)
            return

        index = parent_item.indexOfChild(item)
        if index >= 0:
            parent_item.takeChild(index)
        self._insert_sorted(parent_item, item)

    def _insert_sorted(self, parent_item: Optional[QTreeWidgetItem], item: QTreeWidgetItem) -> None:
        """指定親ノードの子としてソート順を維持しつつ挿入する。"""
        is_directory = bool(item.data(0, Qt.ItemDataRole.UserRole + 1))
        key = self._sort_key(is_directory, item.text(0))

        if parent_item is None:
            insert_index = self.topLevelItemCount()
            for current_index in range(self.topLevelItemCount()):
                current_item = self.topLevelItem(current_index)
                if current_item is None:
                    continue
                current_is_dir = bool(current_item.data(0, Qt.ItemDataRole.UserRole + 1))
                current_key = self._sort_key(current_is_dir, current_item.text(0))
                if key < current_key:
                    insert_index = current_index
                    break
            self.insertTopLevelItem(insert_index, item)
            return

        insert_index = parent_item.childCount()
        for current_index in range(parent_item.childCount()):
            current_item = cast(Optional[QTreeWidgetItem], parent_item.child(current_index))
            if current_item is None:
                continue
            current_is_dir = bool(current_item.data(0, Qt.ItemDataRole.UserRole + 1))
            current_key = self._sort_key(current_is_dir, current_item.text(0))
            if key < current_key:
                insert_index = current_index
                break
        parent_item.insertChild(insert_index, item)
