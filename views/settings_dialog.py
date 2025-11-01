from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from settings.model import SettingsModel


class SettingsDialog(QDialog):
    """OpenAI設定を入力するためのダイアログ。"""

    def __init__(
        self,
        settings_model: Optional[SettingsModel] = None,
        *,
        parent: Optional[QWidget] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """UIを構築してイベント結線を行う。

        Args:
            settings_model (Optional[SettingsModel]): 設定保存先モデル。
            parent (Optional[QWidget]): 親ウィジェット。
            logger (Optional[logging.Logger]): 出力先ロガー。
        """
        super().__init__(parent)
        self._settings_model = settings_model
        self._logger = logger or logging.getLogger("my_editor.settings_dialog")
        self.setWindowTitle("OpenAI設定")
        self.setModal(True)

        self._api_key_input = QLineEdit(self)
        self._save_button = QPushButton("保存", self)
        self._cancel_button = QPushButton("キャンセル", self)

        self._build_layout()
        self._bind_actions()
        self._load_initial_values()

    def _build_layout(self) -> None:
        """ウィジェットの配置を構築する。"""
        main_layout = QVBoxLayout(self)
        row = QHBoxLayout()
        row.addWidget(QLabel("APIキー", self))
        row.addWidget(self._api_key_input)
        main_layout.addLayout(row)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self._cancel_button)
        buttons.addWidget(self._save_button)
        main_layout.addLayout(buttons)

    def _bind_actions(self) -> None:
        """ボタン操作のシグナルを接続する。"""
        self._save_button.clicked.connect(self._handle_save)
        self._cancel_button.clicked.connect(self.reject)

    def _load_initial_values(self) -> None:
        """モデルから初期値を読み込む。"""
        if self._settings_model is None:
            return

        try:
            api_key = self._settings_model.get_api_key()
        except Exception:  # noqa: BLE001
            self._logger.exception("APIキーの取得に失敗しました。")
            return

        if api_key is not None:
            self._api_key_input.setText(api_key)

    def _handle_save(self) -> None:
        """保存ボタン押下時の処理を行う。"""
        api_key = self._api_key_input.text().strip()
        if self._settings_model is None:
            self._logger.warning("設定モデルが指定されていないため保存できません。")
            self.accept()
            return

        try:
            self._settings_model.set_api_key(api_key)
        except Exception:  # noqa: BLE001
            self._logger.exception("APIキーの保存に失敗しました。")
            return

        self._logger.info("APIキーを保存しました。")
        self.accept()

    @property
    def api_key_input(self) -> QLineEdit:
        """APIキー入力欄を返す。"""
        return self._api_key_input

    @property
    def save_button(self) -> QPushButton:
        """保存ボタンを返す。"""
        return self._save_button

    @property
    def cancel_button(self) -> QPushButton:
        """キャンセルボタンを返す。"""
        return self._cancel_button
