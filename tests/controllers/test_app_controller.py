from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTreeWidgetItem

from controllers.app_controller import AppController
from controllers.event_bus import EventBus
from controllers.file_controller import FileController
from views.main_window import MainWindow


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

    def save_current_file(self) -> Path | None:
        self.invoked = True
        return self._save_result

    def open_file(self, path: Path) -> int:
        self.opened.append(path)
        return 0

    def close_current_tab(self) -> Path | None:
        self.closed = True
        return None


def _build_controller(
    qt_app: QApplication,
    main_window: MainWindow,
    *,
    event_bus: EventBus | None = None,
    file_controller: FileController | None = None,
) -> AppController:
    """テスト用のAppControllerを生成するヘルパー。"""
    bus = event_bus or EventBus()
    return AppController(
        qt_app,
        logging.getLogger("test.app_controller"),
        event_bus=bus,
        window_factory=lambda: main_window,
        file_controller=file_controller,
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
