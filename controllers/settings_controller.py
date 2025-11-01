from __future__ import annotations

import logging
from typing import Callable, Optional

from PySide6.QtWidgets import QWidget

from settings.model import SettingsModel
from views.settings_dialog import SettingsDialog


DialogFactory = Callable[[SettingsModel, Optional[QWidget], Optional[logging.Logger]], SettingsDialog]


class SettingsController:
    """設定ダイアログとモデル間の調停を行うコントローラ。"""

    def __init__(
        self,
        *,
        settings_model: Optional[SettingsModel] = None,
        dialog_factory: Optional[DialogFactory] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """依存オブジェクトを受け取り初期化する。"""
        self._logger = logger or logging.getLogger("my_editor.settings_controller")
        self._settings_model = settings_model or SettingsModel()
        self._dialog_factory: DialogFactory = dialog_factory or self._default_dialog_factory

    def open_dialog(self, parent: QWidget | None = None) -> bool:
        """設定ダイアログを開き操作結果を返す。"""
        dialog = self._dialog_factory(self._settings_model, parent, self._logger)
        result = dialog.exec()
        return result == dialog.DialogCode.Accepted

    def _default_dialog_factory(
        self,
        model: SettingsModel,
    parent: QWidget | None = None,
        logger: logging.Logger | None = None,
    ) -> SettingsDialog:
        """SettingsDialogを生成する既定ファクトリ。"""
        return SettingsDialog(model, parent=parent, logger=logger)

    def load_settings_into_dialog(self, dialog: SettingsDialog) -> None:
        """設定モデルからダイアログへ値を読み込む。"""
        try:
            api_key = self._settings_model.get_api_key()
        except Exception:  # noqa: BLE001
            self._logger.exception("設定読み込みに失敗しました。")
            return

        if api_key is not None:
            dialog.api_key_input.setText(api_key)

    def save_settings_from_dialog(self, dialog: SettingsDialog) -> None:
        """ダイアログの値をモデルへ保存する。"""
        api_key = dialog.api_key_input.text().strip()
        try:
            self._settings_model.set_api_key(api_key)
        except Exception:  # noqa: BLE001
            self._logger.exception("設定保存に失敗しました。")
            return
        self._logger.info("設定を保存しました。")

    @property
    def model(self) -> SettingsModel:
        """現在の設定モデルを返す。"""
        return self._settings_model
