from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # PySide6の遅延インポートに対応するために位置を調整

from main import main


def _cleanup_logger_handlers() -> None:
    """テスト実行後にロガーハンドラを全て除去する。"""
    logger = logging.getLogger("my_editor")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


@pytest.fixture(name="qt_app_cleanup")
def fixture_qt_app_cleanup() -> Generator[None, None, None]:
    """テスト前後でQApplicationインスタンスをクリーンに保つ。"""
    # 事前に既存インスタンスがあれば終了して環境を整える。
    app = QApplication.instance()
    if app is not None:
        app.quit()

    # テスト本体の実行を行う。
    yield

    # テスト完了後にインスタンスとロガーをクリーンアップする。
    app = QApplication.instance()
    if app is not None:
        app.quit()
    _cleanup_logger_handlers()


@pytest.mark.usefixtures("qt_app_cleanup")
def test_main_creates_app(tmp_path: Path) -> None:
    """main関数がQtアプリケーションを初期化できることを確認する。"""
    # ログ出力先を一時ディレクトリに設定する。
    log_file = tmp_path / "app.log"

    # イベントループを開始せずにmainを呼び出し初期化のみ行う。
    exit_code = main(argv=[], execute=False, log_path=log_file)

    # 正常終了コードを確認する。
    assert exit_code == 0

    # ログファイルが作成されていることを確認する。
    assert log_file.exists()

    # QApplicationインスタンスが生成されていることを確認する。
    app = QApplication.instance()
    assert app is not None