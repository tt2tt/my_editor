from __future__ import annotations

import logging
import sys
from pathlib import Path
from types import TracebackType
from typing import Callable, Sequence, cast

from PySide6.QtWidgets import QApplication, QMessageBox
ExceptionHook = Callable[[type[BaseException], BaseException, TracebackType | None], None]


def install_exception_hook(logger: logging.Logger) -> ExceptionHook:
    """グローバル例外ハンドラを登録してログ出力とユーザー通知を行う。

    Args:
        logger (logging.Logger): 例外発生時に利用するアプリケーションロガー。

    Returns:
        ExceptionHook: 置き換え前の例外ハンドラ。
    """

    # 既存の例外ハンドラを保持し、必要に応じて委譲できるようにする。
    previous_hook = sys.excepthook

    def _show_error_dialog(message: str) -> None:
        """ユーザーへエラーダイアログを表示する。"""
        app = QApplication.instance()
        if app is None:
            # QApplicationが未初期化の場合は標準エラー出力で通知する。
            sys.stderr.write("予期しないエラーが発生しました。ログを確認してください。\n")
            sys.stderr.write(f"詳細: {message}\n")
            return

        parent = QApplication.activeWindow()
        dialog = QMessageBox(parent=parent)
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setWindowTitle("エラー")
        dialog.setText("予期しないエラーが発生しました。")
        dialog.setInformativeText(message)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()

    def _handle_exception(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        """未処理例外を捕捉してログと通知を実施する。"""
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            previous_hook(exc_type, exc_value, exc_traceback)
            return

        logger.critical("未処理例外が発生しました。", exc_info=(exc_type, exc_value, exc_traceback))
        _show_error_dialog(str(exc_value))

    sys.excepthook = _handle_exception
    return previous_hook

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
        return cast(QApplication, existing), False

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

    # グローバル例外ハンドラを設定する。
    install_exception_hook(logger)

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
