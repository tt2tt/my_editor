from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtWidgets import QApplication

from views.main_window import MainWindow


class AppController:
    """アプリケーション全体の起動と終了を制御するコントローラ。"""

    def __init__(self, app: QApplication, logger: logging.Logger) -> None:
        """依存オブジェクトを受け取り初期化する。

        Args:
            app (QApplication): Qtアプリケーションインスタンス。
            logger (logging.Logger): アプリ共通ロガー。
        """
        # 渡された依存を保持し、ウィンドウ生成を行う。
        self._app = app
        self._logger = logger
        self._window: Optional[MainWindow] = None

        # メインウィンドウを構築する。
        self._initialize_window()

    def _initialize_window(self) -> None:
        """メインウィンドウを生成して初期状態を整える。"""
        # ウィンドウを生成し、後続処理で利用できるように保持する。
        self._window = MainWindow()
        self._logger.info("メインウィンドウを初期化しました。")

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
