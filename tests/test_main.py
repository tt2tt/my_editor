from __future__ import annotations

import logging
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # PySide6の遅延インポートに対応するために位置を調整

from logging_config import setup_logging
from main import install_exception_hook, main


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


@pytest.mark.usefixtures("qt_app_cleanup")
def test_exception_hook_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """グローバル例外ハンドラがログ出力とユーザー通知を行うことを確認する。"""
    # テスト用にログファイルを準備する。
    log_file = tmp_path / "exception.log"
    logger = setup_logging(log_file)

    # QMessageBoxをモック化してUI表示を抑制する。
    captured: dict[str, object] = {"shown": False, "message": ""}

    class DummyMessageBox:
        """テスト用のモックメッセージボックス。"""

        class Icon:
            """QMessageBox.Icon の簡易モック。"""

            Critical = object()

        class StandardButton:
            """QMessageBox.StandardButton の簡易モック。"""

            Ok = object()

        def __init__(self, parent: object | None = None) -> None:
            self._parent = parent

        def setIcon(self, icon: object) -> None:
            captured["icon"] = icon

        def setWindowTitle(self, title: str) -> None:
            captured["title"] = title

        def setText(self, text: str) -> None:
            captured["text"] = text

        def setInformativeText(self, text: str) -> None:
            captured["message"] = text

        def setStandardButtons(self, buttons: object) -> None:
            captured["buttons"] = buttons

        def exec(self) -> int:
            captured["shown"] = True
            return 0

    monkeypatch.setattr("main.QMessageBox", DummyMessageBox)

    # QApplicationインスタンスを確実に用意する。
    if QApplication.instance() is None:
        QApplication([])

    # 例外ハンドラをインストールしてテスト用に実行する。
    previous_hook = install_exception_hook(logger)
    try:
        raise RuntimeError("テスト例外")
    except RuntimeError:
        exc_type, exc_value, exc_tb = sys.exc_info()
        assert exc_type is not None
        assert exc_value is not None
        sys.excepthook(exc_type, exc_value, exc_tb)
    finally:
        sys.excepthook = previous_hook

    # ログファイルへ書き出された内容を検証する。
    for handler in logger.handlers:
        handler.flush()

    log_text = log_file.read_text(encoding="utf-8")
    assert "未処理例外が発生しました。" in log_text
    assert "RuntimeError" in log_text

    # ユーザー通知が呼び出されたことを確認する。
    assert bool(captured["shown"])
    assert "テスト例外" in str(captured["message"])
