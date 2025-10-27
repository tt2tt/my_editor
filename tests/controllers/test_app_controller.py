from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTreeWidgetItem, QWidget

from controllers.app_controller import AppController
from controllers.ai_controller import AIController
from controllers.event_bus import EventBus
from controllers.file_controller import FileController
from controllers.settings_controller import SettingsController
from settings.model import SettingsModel
from views.main_window import MainWindow
from exceptions import AIIntegrationError


class _StubSettingsModel:
    """設定情報をメモリ上で保持するテスト用モデル。"""

    def __init__(self) -> None:
        self.api_key: str | None = "dummy-key"

    def get_api_key(self) -> str | None:
        return self.api_key

    def set_api_key(self, key: str) -> None:
        self.api_key = key


class _StubAIController:
    """AIコントローラの呼び出しを検証するスタブ。"""

    def __init__(self) -> None:
        self.received: list[str] = []
        self.reset_called = False
        self.response = "stub-response"
        self.raise_error: Exception | None = None

    def handle_chat_submit(self, message: str) -> str:
        if self.raise_error is not None:
            raise self.raise_error
        self.received.append(message)
        return self.response

    def reset_client(self) -> None:
        self.reset_called = True


@pytest.fixture(name="qt_app")
def fixture_qt_app() -> Generator[QApplication, None, None]:
    """テスト全体で共有するQApplicationインスタンスを準備する。"""
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    app = cast(QApplication, app_instance)
    yield app


@pytest.fixture(name="main_window")
def fixture_main_window(qt_app: QApplication) -> Generator[MainWindow, None, None]:
    """MainWindowインスタンスを生成しテスト後に廃棄する。"""
    window = MainWindow()
    yield window
    window.close()
    window.deleteLater()


class _StubFileController:
    """保存呼び出しの記録を行うテスト用スタブ。"""

    def __init__(self, *, save_result: Path | None) -> None:
        self.invoked = False
        self.opened: list[Path] = []
        self.closed = False
        self._save_result = save_result
        self.new_file_calls = 0

    def save_current_file(self) -> Path | None:
        self.invoked = True
        return self._save_result

    def open_file(self, path: Path) -> int:
        self.opened.append(path)
        return 0

    def close_current_tab(self) -> Path | None:
        self.closed = True
        return None

    def create_new_file(self) -> Path:
        self.new_file_calls += 1
        return Path(f"untitled-{self.new_file_calls}.txt")


class _StubSettingsController:
    """設定ダイアログ呼び出しを記録するスタブ。"""

    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.parent: QWidget | None = None
        self._settings_model = _StubSettingsModel()

    def open_dialog(self, parent: QWidget | None = None) -> bool:
        self.parent = parent
        return self.result

    @property
    def model(self) -> SettingsModel:
        return cast(SettingsModel, self._settings_model)


def _build_controller(
    qt_app: QApplication,
    main_window: MainWindow,
    *,
    event_bus: EventBus | None = None,
    file_controller: FileController | None = None,
    settings_controller: SettingsController | None = None,
    ai_controller: AIController | None = None,
) -> AppController:
    """テスト用のAppControllerを生成するヘルパー。"""
    bus = event_bus or EventBus()
    ai_ctrl = ai_controller or cast(AIController, _StubAIController())
    settings_ctrl = settings_controller or cast(SettingsController, _StubSettingsController())
    return AppController(
        qt_app,
        logging.getLogger("test.app_controller"),
        event_bus=bus,
        window_factory=lambda: main_window,
        file_controller=file_controller,
        settings_controller=settings_ctrl,
        ai_controller=ai_ctrl,
    )


def test_wire_events_emits_tab_change(
    qt_app: QApplication, main_window: MainWindow
) -> None:
    """タブ変更時にイベントバスへ通知されることを検証する。"""
    bus = EventBus()
    _build_controller(qt_app, main_window, event_bus=bus)
    received: list[dict[str, object] | None] = []
    bus.subscribe(AppController.EVENT_TAB_CHANGED, lambda payload: received.append(payload))

    main_window.tab_widget.currentChanged.emit(3)
    qt_app.processEvents()

    assert received
    assert received[0] == {"index": 3, "tab_count": main_window.tab_widget.count()}


def test_new_action_triggers_blank_file(
    qt_app: QApplication,
    main_window: MainWindow,
) -> None:
    """新規ファイルアクションでファイルコントローラの処理が呼び出されることを検証する。"""
    stub_controller = _StubFileController(save_result=None)
    _build_controller(
        qt_app,
        main_window,
        file_controller=cast(FileController, stub_controller),
    )

    main_window.action_new_file.trigger()
    qt_app.processEvents()

    assert stub_controller.new_file_calls == 1


def test_wire_events_emits_folder_selection(
    qt_app: QApplication, main_window: MainWindow, tmp_path: Path
) -> None:
    """フォルダ選択変更がイベントバスに反映されることを検証する。"""
    bus = EventBus()
    _build_controller(qt_app, main_window, event_bus=bus)
    captured: list[dict[str, object] | None] = []
    bus.subscribe(AppController.EVENT_FOLDER_SELECTED, lambda payload: captured.append(payload))

    item = QTreeWidgetItem(["dummy"])
    main_window.folder_view.addTopLevelItem(item)
    target = tmp_path / "sample"
    item.setData(0, Qt.ItemDataRole.UserRole, str(target))
    main_window.folder_view.setCurrentItem(item)
    qt_app.processEvents()

    assert captured
    payload = captured[0]
    assert payload is not None
    assert payload["path"] == target


def test_folder_selection_opens_file(
    qt_app: QApplication,
    main_window: MainWindow,
    tmp_path: Path,
) -> None:
    """フォルダツリーでファイルを選択するとファイルが開かれることを検証する。"""
    target = (tmp_path / "example.txt").resolve()
    target.write_text("sample")
    stub_controller = _StubFileController(save_result=None)
    _build_controller(
        qt_app,
        main_window,
        file_controller=cast(FileController, stub_controller),
    )

    item = QTreeWidgetItem(["dummy"])
    item.setData(0, Qt.ItemDataRole.UserRole, str(target))
    main_window.folder_view.addTopLevelItem(item)
    main_window.folder_view.setCurrentItem(item)
    qt_app.processEvents()

    assert stub_controller.opened == [target]


def test_settings_action_opens_dialog(
    qt_app: QApplication,
    main_window: MainWindow,
) -> None:
    """設定アクションが設定ダイアログを開くことを検証する。"""
    stub_settings = _StubSettingsController(result=True)
    _build_controller(
        qt_app,
        main_window,
        settings_controller=cast(SettingsController, stub_settings),
    )

    main_window.action_open_settings.trigger()
    qt_app.processEvents()

    assert stub_settings.parent is main_window


def test_wire_events_handles_save_request(
    qt_app: QApplication, main_window: MainWindow, tmp_path: Path
) -> None:
    """保存イベントがファイルコントローラへ委譲されることを検証する。"""
    save_path = (tmp_path / "result.txt").resolve()
    stub_controller = _StubFileController(save_result=save_path)
    bus = EventBus()
    _build_controller(
        qt_app,
        main_window,
        event_bus=bus,
        file_controller=cast(FileController, stub_controller),
    )
    saved_events: list[dict[str, object] | None] = []
    bus.subscribe(AppController.EVENT_FILE_SAVED, lambda payload: saved_events.append(payload))

    bus.publish(AppController.EVENT_FILE_SAVE_REQUESTED)
    qt_app.processEvents()

    assert stub_controller.invoked is True
    assert saved_events
    payload = saved_events[0]
    assert payload is not None
    assert payload["path"] == save_path


def test_close_action_triggers_file_controller(
    qt_app: QApplication,
    main_window: MainWindow,
    tmp_path: Path,
) -> None:
    """タブを閉じるアクションでファイルコントローラが呼び出されることを検証する。"""
    stub_controller = _StubFileController(save_result=None)
    controller = _build_controller(
        qt_app,
        main_window,
        file_controller=cast(FileController, stub_controller),
    )

    main_window.action_close_tab.trigger()
    qt_app.processEvents()

    assert stub_controller.closed is True


def test_open_action_triggers_file_controller(
    qt_app: QApplication,
    main_window: MainWindow,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """開くアクションでファイルコントローラの処理が実行されることを検証する。"""
    target = (tmp_path / "example.txt").resolve()
    stub_controller = _StubFileController(save_result=None)
    controller = _build_controller(
        qt_app,
        main_window,
        file_controller=cast(FileController, stub_controller),
    )

    monkeypatch.setattr(controller, "_prompt_file_to_open", lambda: target)

    main_window.action_open_file.trigger()
    qt_app.processEvents()

    assert stub_controller.opened == [target]


def test_chat_submission_delegates_to_ai_controller(
    qt_app: QApplication,
    main_window: MainWindow,
) -> None:
    """チャット送信がAIコントローラへ委譲されることを検証する。"""
    ai_stub = _StubAIController()
    _build_controller(
        qt_app,
        main_window,
        ai_controller=cast(AIController, ai_stub),
    )

    main_window.chat_submitted.emit("こんにちは")
    qt_app.processEvents()

    assert ai_stub.received == ["こんにちは"]
    assert main_window.statusBar().currentMessage() == "AI応答: stub-response"


def test_chat_error_displays_status_message(
    qt_app: QApplication,
    main_window: MainWindow,
) -> None:
    """AI呼び出しで例外が発生した場合にエラーメッセージが表示されることを検証する。"""
    ai_stub = _StubAIController()
    ai_stub.raise_error = AIIntegrationError("APIキーが未設定です。")
    _build_controller(
        qt_app,
        main_window,
        ai_controller=cast(AIController, ai_stub),
    )

    main_window.chat_submitted.emit("テスト")
    qt_app.processEvents()

    assert main_window.statusBar().currentMessage() == "チャットエラー: APIキーが未設定です。"


def test_settings_acceptation_resets_ai_client(
    qt_app: QApplication,
    main_window: MainWindow,
) -> None:
    """設定保存後にAIクライアントがリセットされることを検証する。"""
    ai_stub = _StubAIController()
    stub_settings = _StubSettingsController(result=True)
    _build_controller(
        qt_app,
        main_window,
        settings_controller=cast(SettingsController, stub_settings),
        ai_controller=cast(AIController, ai_stub),
    )

    main_window.action_open_settings.trigger()
    qt_app.processEvents()

    assert ai_stub.reset_called is True


def test_settings_cancel_does_not_reset_ai_client(
    qt_app: QApplication,
    main_window: MainWindow,
) -> None:
    """設定ダイアログがキャンセルされた場合にAIクライアントが保持されることを検証する。"""
    ai_stub = _StubAIController()
    stub_settings = _StubSettingsController(result=False)
    _build_controller(
        qt_app,
        main_window,
        settings_controller=cast(SettingsController, stub_settings),
        ai_controller=cast(AIController, ai_stub),
    )

    main_window.action_open_settings.trigger()
    qt_app.processEvents()

    assert ai_stub.reset_called is False
