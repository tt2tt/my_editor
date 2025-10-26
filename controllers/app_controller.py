from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from controllers.event_bus import EventBus, Payload
from views.main_window import MainWindow

if TYPE_CHECKING:
    from controllers.file_controller import FileController
    from controllers.folder_controller import FolderController
    from controllers.tab_controller import TabController


class AppController:
    """アプリケーション全体の起動と終了を制御するコントローラ。"""

    EVENT_TAB_CHANGED = "ui.tab.changed"
    EVENT_FOLDER_SELECTED = "ui.folder.selected"
    EVENT_FILE_SAVE_REQUESTED = "command.file.save"
    EVENT_FILE_SAVED = "state.file.saved"

    def __init__(
        self,
        app: QApplication,
        logger: logging.Logger,
        *,
        event_bus: Optional[EventBus] = None,
        window_factory: Optional[Callable[[], MainWindow]] = None,
        file_controller: Optional[FileController] = None,
        folder_controller: Optional[FolderController] = None,
        tab_controller: Optional[TabController] = None,
    ) -> None:
        """依存オブジェクトを受け取り初期化する。

        Args:
            app (QApplication): Qtアプリケーションインスタンス。
            logger (logging.Logger): アプリ共通ロガー。
            event_bus (Optional[EventBus]): イベントディスパッチャ。
            window_factory (Optional[Callable[[], MainWindow]]): ウィンドウ生成用ファクトリ。
            file_controller (Optional[FileController]): ファイル操作コントローラ。
            folder_controller (Optional[FolderController]): フォルダ操作コントローラ。
            tab_controller (Optional[TabController]): タブ操作コントローラ。
        """
        # 渡された依存を保持し、ウィンドウ生成を行う。
        self._app = app
        self._logger = logger
        self._event_bus = event_bus or EventBus(logger)
        self._window_factory = window_factory or MainWindow
        self._window: Optional[MainWindow] = None
        self._file_controller = file_controller
        self._folder_controller = folder_controller
        self._tab_controller = tab_controller

        # メインウィンドウを構築する。
        self._initialize_window()
        self._wire_events()

    def _initialize_window(self) -> None:
        """メインウィンドウを生成して初期状態を整える。"""
        # ウィンドウを生成し、後続処理で利用できるように保持する。
        self._window = self._window_factory()
        self._logger.info("メインウィンドウを初期化しました。")

    def _wire_events(self) -> None:
        """ビューシグナルとイベントバスの結線、およびハンドラ購読を設定する。"""
        if self._window is None:
            raise RuntimeError("ウィンドウが初期化されていません。")

        tab_widget = self._window.tab_widget
        folder_view = self._window.folder_view

        # タブ切り替えイベントをイベントバス経由で通知する。
        tab_widget.currentChanged.connect(self._emit_tab_changed)

        # フォルダ選択変更をイベントバスへ送出する。
        folder_view.itemSelectionChanged.connect(self._emit_folder_selected)

        # 保存要求を購読しファイルコントローラへ委譲する。
        self._event_bus.subscribe(self.EVENT_FILE_SAVE_REQUESTED, self._handle_save_request)

    def _emit_tab_changed(self, index: int) -> None:
        """タブ変更シグナルを受け取りイベントバスへ配信する。"""
        payload: Payload = {"index": index, "tab_count": self._window.tab_widget.count() if self._window else 0}
        self._event_bus.publish(self.EVENT_TAB_CHANGED, payload)
        self._logger.debug("タブ変更イベントを発行しました: %s", payload)

    def _emit_folder_selected(self) -> None:
        """フォルダ選択シグナルからイベントバスへ通知する。"""
        if self._window is None:
            return

        path = self._resolve_selected_path()
        payload: Payload = {"path": path}
        self._event_bus.publish(self.EVENT_FOLDER_SELECTED, payload)
        self._logger.debug("フォルダ選択イベントを発行しました: %s", payload)

    def _handle_save_request(self, payload: Payload) -> None:
        """保存要求イベントを受け取りファイル保存を実行する。"""
        if self._file_controller is None:
            self._logger.warning("ファイルコントローラが未設定のため保存要求を処理できません。")
            return

        try:
            result = self._file_controller.save_current_file()
        except Exception:  # noqa: BLE001
            self._logger.exception("ファイル保存処理中に例外が発生しました。")
            return

        saved_payload: Payload = {"path": result} if result is not None else None
        self._event_bus.publish(self.EVENT_FILE_SAVED, saved_payload)
        self._logger.info("ファイル保存が完了しました。%s", saved_payload)

    def _resolve_selected_path(self) -> Optional[Path]:
        """フォルダビューの選択状態からパス情報を取得する。"""
        if self._window is None:
            return None

        view = self._window.folder_view

        # FolderTreeの場合は専用ヘルパーを利用する。
        current_path = getattr(view, "current_path", None)
        if callable(current_path):
            try:
                resolved = current_path()
                if isinstance(resolved, Path):
                    return resolved
            except Exception:  # noqa: BLE001
                self._logger.debug("フォルダパス取得中にエラーが発生しました。", exc_info=True)

        item = getattr(view, "currentItem", None)
        if callable(item):
            current_item = item()
            if current_item is not None:
                # UserRoleデータが設定されていれば優先する。
                data = current_item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, Path):
                    return data
                if isinstance(data, str):
                    return Path(data)

                text_getter = getattr(current_item, "text", None)
                if callable(text_getter):
                    text = text_getter()
                    if text:
                        return Path(text)

        return None

    def start(self) -> None:
        """アプリケーションを起動してウィンドウを表示する。"""
        # ウィンドウが生成済みであることを確認する。
        if self._window is None:
            raise RuntimeError("ウィンドウが初期化されていません。")

        # ウィンドウ表示と起動ログを出力する。
        self._logger.info("アプリケーションを起動します。")
        self._window.show()

    @property
    def window(self) -> MainWindow:
        """生成済みのメインウィンドウを返す。"""
        if self._window is None:
            raise RuntimeError("ウィンドウが初期化されていません。")
        return self._window

    @property
    def event_bus(self) -> EventBus:
        """アプリケーション全体で共有するイベントバスを返す。"""
        return self._event_bus

    @property
    def file_controller(self) -> Optional[FileController]:
        """現在のファイルコントローラを返す。"""
        return self._file_controller

    @property
    def folder_controller(self) -> Optional[FolderController]:
        """現在のフォルダコントローラを返す。"""
        return self._folder_controller

    @property
    def tab_controller(self) -> Optional[TabController]:
        """現在のタブコントローラを返す。"""
        return self._tab_controller
