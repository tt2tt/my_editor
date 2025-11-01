from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog

from settings.model import SettingsModel
from views.settings_dialog import SettingsDialog


class _StubSettingsModel(SettingsModel):
    """APIキーの保存呼び出しを記録するテスト用スタブ。"""

    def __init__(self, initial_key: str | None = None) -> None:
        super().__init__(storage_path=Path("dummy_settings.json"))
        self.saved_key: str | None = None
        self._initial_key = initial_key

    def get_api_key(self) -> str | None:
        return self._initial_key

    def set_api_key(self, key: str) -> None:
        self.saved_key = key


@pytest.fixture(name="qt_app")
def fixture_qt_app() -> Generator[QApplication, None, None]:
    """QApplicationインスタンスをテスト全体で共有する。"""
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    app = app_instance
    assert isinstance(app, QApplication)
    yield app


def test_save_triggers_model(qt_app: QApplication) -> None:
    """保存ボタンでモデルのset_api_keyが呼び出されることを検証する。"""
    model = _StubSettingsModel(initial_key="initial-key")
    dialog = SettingsDialog(model)

    assert dialog.api_key_input.text() == "initial-key"

    dialog.api_key_input.setText(" updated-key ")
    QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert model.saved_key == "updated-key"
