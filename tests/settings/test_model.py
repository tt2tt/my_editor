from __future__ import annotations

from pathlib import Path

import pytest

from settings.model import SettingsModel


@pytest.fixture()
def settings_path(tmp_path: Path) -> Path:
    """設定モデル用の一時ファイルパスを返す。"""
    return tmp_path / "settings.json"


def test_set_and_get_api_key(settings_path: Path) -> None:
    """APIキーの保存と取得が正しく行えることを検証する。"""
    # モデルを初期化してAPIキーを保存する。
    model = SettingsModel(storage_path=settings_path)
    model.set_api_key("test-key")

    # APIキーが正しく読み込まれることを確認する。
    assert model.get_api_key() == "test-key"


def test_load_settings_returns_empty_dict_when_missing(settings_path: Path) -> None:
    """設定ファイルが存在しない場合は空辞書を返すことを検証する。"""
    # ファイルが無い状態でロードして空辞書になることを確認する。
    model = SettingsModel(storage_path=settings_path)
    assert model.load_settings() == {}


def test_save_settings_persists_data(settings_path: Path) -> None:
    """save_settingsが辞書データを永続化できることを検証する。"""
    # 任意の設定を保存した後、再読み込みで同じ内容になることを確認する。
    model = SettingsModel(storage_path=settings_path)
    data = {"api_key": "abc", "theme": "dark"}
    model.save_settings(data)

    assert model.load_settings() == data
