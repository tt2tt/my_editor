from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog

from controllers.ai_controller import AIController
from controllers.event_bus import EventBus, Payload
from controllers.file_controller import FileController
from controllers.folder_controller import FolderController
from controllers.settings_controller import SettingsController
from controllers.tab_controller import TabController
from models.file_model import FileModel
from models.folder_model import FolderModel
from models.tab_model import TabState
from views.folder_tree import FolderTree
from views.main_window import MainWindow
from exceptions import FileOperationError, AIIntegrationError


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
        settings_controller: Optional[SettingsController] = None,
        tab_controller: Optional[TabController] = None,
        ai_controller: Optional[AIController] = None,
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
        self._settings_controller = settings_controller
        self._tab_controller = tab_controller
        self._ai_controller = ai_controller
        self._tab_state: Optional[TabState] = None

        # メインウィンドウを構築する。
        self._initialize_window()
        self._initialize_controllers()
        self._wire_events()

    def _initialize_window(self) -> None:
        """メインウィンドウを生成して初期状態を整える。"""
        # ウィンドウを生成し、後続処理で利用できるように保持する。
        self._window = self._window_factory()
        self._logger.info("メインウィンドウを初期化しました。")

    def _initialize_controllers(self) -> None:
        """UIアクションと各コントローラを結び付ける。"""
        if self._window is None:
            raise RuntimeError("ウィンドウが初期化されていません。")

        tab_view = self._window.tab_widget
        folder_view: FolderTree = self._window.folder_view

        # 既存の依存が無い場合は標準構成を生成する。
        if self._tab_state is None:
            self._tab_state = TabState(self._logger.getChild("tab_state"))

        if self._tab_controller is None:
            self._tab_controller = TabController(
                self._tab_state,
                tab_view,
                logger=self._logger.getChild("tab_controller"),
            )

        if self._file_controller is None:
            file_model = FileModel(self._logger.getChild("file_model"))
            self._file_controller = FileController(
                file_model,
                self._tab_state,
                tab_view,
                logger=self._logger.getChild("file_controller"),
            )

        if self._folder_controller is None:
            folder_model = FolderModel(self._logger.getChild("folder_model"))
            self._folder_controller = FolderController(
                folder_model,
                folder_view,
                logger=self._logger.getChild("folder_controller"),
            )

        if self._settings_controller is None:
            self._settings_controller = SettingsController(
                logger=self._logger.getChild("settings_controller")
            )

        settings_model = getattr(self._settings_controller, "model", None)

        if self._ai_controller is None:
            self._ai_controller = AIController(
                logger=self._logger.getChild("ai_controller"),
                settings_model=settings_model,
            )

        open_action = getattr(self._window, "action_open_file", None)
        if open_action is not None:
            open_action.triggered.connect(self._handle_open_file_action)

        new_action = getattr(self._window, "action_new_file", None)
        if new_action is not None:
            new_action.triggered.connect(self._handle_new_file_action)

        open_folder_action = getattr(self._window, "action_open_folder", None)
        if open_folder_action is not None:
            open_folder_action.triggered.connect(self._handle_open_folder_action)

        save_action = getattr(self._window, "action_save_file", None)
        if save_action is not None:
            save_action.triggered.connect(self._emit_save_requested)

        close_action = getattr(self._window, "action_close_tab", None)
        if close_action is not None:
            close_action.triggered.connect(self._handle_close_tab_action)

        settings_action = getattr(self._window, "action_open_settings", None)
        if settings_action is not None:
            settings_action.triggered.connect(self._handle_open_settings_action)

        chat_signal = getattr(self._window, "chat_submitted", None)
        if chat_signal is not None:
            chat_signal.connect(self._handle_chat_submitted)

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
        self._open_file_from_folder_selection(path)

    def _open_file_from_folder_selection(self, path: Optional[Path]) -> None:
        """フォルダツリーで選択されたファイルを開く。"""
        if path is None:
            return

        normalized = path.expanduser().resolve(strict=False)

        if not normalized.is_file():
            return

        if self._file_controller is None:
            self._logger.warning("フォルダ選択からファイルを開けません。ファイルコントローラが未設定です。")
            return

        try:
            self._file_controller.open_file(normalized)
        except Exception:  # noqa: BLE001
            self._logger.exception("フォルダ選択からのファイルオープンに失敗しました。")

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

    def _handle_open_file_action(self) -> None:
        """ファイルを開くアクションを処理する。"""
        if self._file_controller is None:
            self._logger.warning("ファイルコントローラが未設定のため開く操作を処理できません。")
            return

        selected = self._prompt_file_to_open()
        if selected is None:
            self._logger.debug("ファイル選択がキャンセルされました。")
            return

        try:
            self._file_controller.open_file(selected)
        except Exception:  # noqa: BLE001
            self._logger.exception("ファイルを開く処理中に例外が発生しました。")

    def _handle_new_file_action(self) -> None:
        """新規ファイル作成アクションを処理する。"""
        if self._file_controller is None:
            self._logger.warning("ファイルコントローラが未設定のため新規作成を処理できません。")
            return

        try:
            self._file_controller.create_new_file()
        except Exception:  # noqa: BLE001
            self._logger.exception("新規ファイル作成中に例外が発生しました。")

    def _handle_open_folder_action(self) -> None:
        """フォルダを開くアクションを処理する。"""
        if self._folder_controller is None:
            self._logger.warning("フォルダコントローラが未設定のためフォルダを開けません。")
            return

        selected = self._prompt_folder_to_open()
        if selected is None:
            self._logger.debug("フォルダ選択がキャンセルされました。")
            return

        try:
            self._folder_controller.load_initial_tree(selected)
        except FileOperationError:
            self._logger.exception("フォルダツリーの初期化に失敗しました。")
        except Exception:  # noqa: BLE001
            self._logger.exception("フォルダ読み込み処理中に予期せぬエラーが発生しました。")

    def _handle_close_tab_action(self) -> None:
        """タブを閉じるアクションを処理する。"""
        if self._file_controller is None:
            self._logger.warning("ファイルコントローラが未設定のためタブを閉じられません。")
            return

        try:
            closed_path = self._file_controller.close_current_tab()
        except Exception:  # noqa: BLE001
            self._logger.exception("タブを閉じる処理中に例外が発生しました。")
            return

        if closed_path is None:
            self._logger.debug("タブを閉じる対象が存在しませんでした。")
        else:
            self._logger.info("タブを閉じました: %s", closed_path)

    def _handle_open_settings_action(self) -> None:
        """設定ダイアログを開くアクションを処理する。"""
        if self._settings_controller is None:
            self._logger.warning("設定コントローラが未設定のためダイアログを開けません。")
            return

        if self._window is None:
            self._logger.warning("ウィンドウが初期化されていないため設定を開けません。")
            return

        try:
            accepted = self._settings_controller.open_dialog(parent=self._window)
        except Exception:  # noqa: BLE001
            self._logger.exception("設定ダイアログの表示中に例外が発生しました。")
            return

        if accepted:
            self._logger.info("設定ダイアログで変更が保存されました。")
            if self._ai_controller is not None:
                self._ai_controller.reset_client()
        else:
            self._logger.debug("設定ダイアログはキャンセルされました。")

    def _handle_chat_submitted(self, message: str) -> None:
        """チャット入力をAIコントローラへ委譲する。"""
        trimmed = message.strip()

        if not trimmed:
            if self._window is not None:
                self._window.show_chat_error("メッセージを入力してください。")
            return

        if self._ai_controller is None:
            self._logger.warning("AIコントローラが未設定のためチャットを処理できません。")
            if self._window is not None:
                self._window.show_chat_error("AI機能が利用できません。")
            return

        try:
            response = self._ai_controller.handle_chat_submit(trimmed)
        except AIIntegrationError as exc:
            self._logger.error("AI応答の取得に失敗しました。", exc_info=exc)
            if self._window is not None:
                self._window.show_chat_error(str(exc))
            return
        except Exception:  # noqa: BLE001
            self._logger.exception("チャット処理中に予期せぬ例外が発生しました。")
            if self._window is not None:
                self._window.show_chat_error("AI応答の取得中にエラーが発生しました。")
            return

        if self._window is not None:
            self._window.show_chat_response(response)

    def _prompt_file_to_open(self) -> Optional[Path]:
        """ファイルを開く際の選択ダイアログを表示する。"""
        if self._window is None:
            return None

        file_path, _ = QFileDialog.getOpenFileName(self._window, "ファイルを開く")
        if not file_path:
            return None

        return Path(file_path).expanduser().resolve(strict=False)

    def _prompt_folder_to_open(self) -> Optional[Path]:
        """フォルダ選択ダイアログを表示する。"""
        if self._window is None:
            return None

        directory = QFileDialog.getExistingDirectory(self._window, "フォルダを開く")
        if not directory:
            return None

        return Path(directory).expanduser().resolve(strict=False)

    def _emit_save_requested(self) -> None:
        """保存要求イベントをイベントバスへ送出する。"""
        self._event_bus.publish(self.EVENT_FILE_SAVE_REQUESTED, None)

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
    def settings_controller(self) -> Optional[SettingsController]:
        """現在の設定コントローラを返す。"""
        return self._settings_controller

    @property
    def tab_controller(self) -> Optional[TabController]:
        """現在のタブコントローラを返す。"""
        return self._tab_controller

    @property
    def ai_controller(self) -> Optional[AIController]:
        """現在のAIコントローラを返す。"""
        return self._ai_controller
