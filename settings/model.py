from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

SETTINGS_FILE = Path.home() / ".my_editor" / "settings.json"


class SettingsModel:
    """アプリ全体で利用する設定を管理するモデル。"""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """設定ストレージのパスを初期化する。

        Args:
            storage_path (Optional[Path]): 設定ファイルの保存先。省略時はユーザーディレクトリ配下。
        """
        # ストレージパスを決定し、親ディレクトリの存在を保証する。
        self._storage_path = (storage_path or SETTINGS_FILE).expanduser().resolve()
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)

    def load_settings(self) -> Dict[str, Any]:
        """設定ファイルから内容を読み込む。

        Returns:
            Dict[str, Any]: 設定データ。ファイルが存在しない場合は空辞書。
        """
        if not self._storage_path.exists():
            return {}

        with self._storage_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def save_settings(self, data: Dict[str, Any]) -> None:
        """設定データをファイルへ書き込む。

        Args:
            data (Dict[str, Any]): 保存対象の設定辞書。
        """
        with self._storage_path.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)

    def get_api_key(self) -> Optional[str]:
        """設定からAPIキーを取得する。

        Returns:
            Optional[str]: APIキー。未設定の場合はNone。
        """
        settings = self.load_settings()
        return settings.get("api_key")

    def set_api_key(self, key: str) -> None:
        """APIキーを設定ファイルへ保存する。

        Args:
            key (str): 保存するAPIキー。
        """
        settings = self.load_settings()
        settings["api_key"] = key
        self.save_settings(settings)
