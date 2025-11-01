from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QWidget

from controllers.settings_controller import SettingsController
from settings.model import SettingsModel
from views.settings_dialog import SettingsDialog


class _StubDialog(SettingsDialog):
    """保存状態と入力値をテスト用に記録するスタブ。"""

    def __init__(
        self,
        model: SettingsModel | None,
        *,
        parent: QWidget | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(model, parent=parent, logger=logger)
        self._executed = False

    def exec(self) -> int:
        self._executed = True
        return SettingsDialog.DialogCode.Accepted

    @property
    def executed(self) -> bool:
        return self._executed


class _StubSettingsModel(SettingsModel):
    """設定の入出力を記録するテスト用スタブ。"""

    def __init__(self) -> None:
        super().__init__(storage_path=Path("dummy_settings.json"))
        self.saved_value: str | None = None
        self._api_key: str | None = "initial"

    def get_api_key(self) -> str | None:
        return self._api_key

    def set_api_key(self, key: str) -> None:
        self.saved_value = key
        self._api_key = key


@pytest.fixture(name="qt_app")
def fixture_qt_app() -> Generator[QApplication, None, None]:
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    app = app_instance
    assert isinstance(app, QApplication)
    yield app


def test_load_settings_calls_model(qt_app: QApplication) -> None:
    model = _StubSettingsModel()
    controller = SettingsController(settings_model=model)
    dialog = SettingsDialog(model)

    controller.load_settings_into_dialog(dialog)

    assert dialog.api_key_input.text() == "initial"


def test_save_settings_calls_model(qt_app: QApplication) -> None:
    model = _StubSettingsModel()
    controller = SettingsController(settings_model=model)
    dialog = SettingsDialog(model)
    dialog.api_key_input.setText(" saved ")

    controller.save_settings_from_dialog(dialog)

    assert model.saved_value == "saved"


def test_open_dialog_uses_factory(qt_app: QApplication) -> None:
    model = _StubSettingsModel()

    created: list[_StubDialog] = []

    def factory(
        settings_model: SettingsModel,
        parent: QWidget | None = None,
        logger: logging.Logger | None = None,
    ) -> SettingsDialog:
        dialog = _StubDialog(settings_model, parent=parent, logger=logger)
        created.append(dialog)
        return dialog

    controller = SettingsController(settings_model=model, dialog_factory=factory)
    result = controller.open_dialog()

    assert result is True
    assert created and created[0].executed is True
