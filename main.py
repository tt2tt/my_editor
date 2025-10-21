from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Sequence

from PySide6.QtWidgets import QApplication

from controllers.app_controller import AppController
from logging_config import setup_logging


def _create_application(argv: Sequence[str] | None) -> tuple[QApplication, bool]:
    """QApplicationを取得または生成する。

    Args:
        argv (Sequence[str] | None): アプリケーション引数。

    Returns:
        tuple[QApplication, bool]: アプリインスタンスと新規生成したかどうかのフラグ。
    """
    # 既存インスタンスがあれば再利用する。
    existing = QApplication.instance()
    if existing is not None:
        return existing, False

    # 新規にアプリケーションを生成する。
    app = QApplication(list(argv) if argv is not None else sys.argv)
    return app, True


def _apply_dark_theme(app: QApplication, logger: logging.Logger) -> None:
    """qdarkstyleを適用してダークテーマを有効にする。

    Args:
        app (QApplication): Qtアプリケーションインスタンス。
        logger (logging.Logger): ログ出力用ロガー。
    """
    try:
        import qdarkstyle
    except ImportError:
        # qdarkstyleが見つからない場合は警告を出して処理を継続する。
        logger.warning("qdarkstyleを読み込めなかったため、デフォルトテーマを使用します。")
        return

    # PySide6用のスタイルシートを適用する。
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyside6"))


def main(argv: Sequence[str] | None = None, *, execute: bool = True, log_path: Path | None = None) -> int:
    """アプリケーションを初期化して起動する。

    Args:
        argv (Sequence[str] | None): コマンドライン引数。Noneの場合はsys.argvを利用する。
        execute (bool): イベントループを開始するかどうか。
        log_path (Path | None): ログファイルの書き出し先。Noneの場合はデフォルトパスを利用する。

    Returns:
        int: アプリケーションの終了コード。
    """
    # ログファイルパスを決定しロガーを準備する。
    resolved_log_path = (log_path or (Path.cwd() / "logs" / "application.log")).resolve()
    logger = setup_logging(resolved_log_path)

    # QApplicationを取得または生成する。
    app, owns_app = _create_application(argv)

    # ダークテーマを適用して見た目を整える。
    _apply_dark_theme(app, logger)

    # コントローラを生成してアプリの起動準備を行う。
    controller = AppController(app, logger)
    controller.start()
    logger.info("アプリケーションの初期化が完了しました。")

    # テスト時はイベントループを開始せずに終了コード0を返す。
    if not execute:
        return 0

    # スクリプト実行時はイベントループを開始し終了コードを返す。
    if owns_app:
        return app.exec()

    # 既存アプリに委ねる場合は正常終了を返す。
    return 0


if __name__ == "__main__":
    sys.exit(main())
