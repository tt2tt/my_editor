from __future__ import annotations

import logging
from pathlib import Path

import pytest

from logging_config import setup_logging


def _cleanup_logger_handlers(logger_name: str) -> None:
    """指定ロガーのハンドラを全て除去してテスト間の干渉を防ぐ。"""
    logger = logging.getLogger(logger_name)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_setup_logging_creates_file(tmp_path: Path) -> None:
    """setup_loggingがログファイルを生成し記録できることを検証する。

    Args:
        tmp_path (Path): Pytestの一時ディレクトリ。
    """
    # ログ出力用ファイルパスを作成する。
    log_file = tmp_path / "my_editor.log"

    # ロガーを構築してメッセージを出力する。
    logger = setup_logging(log_path=log_file)
    logger.info("テストメッセージ")

    # 各ハンドラをフラッシュしてファイルへ書き出す。
    for handler in logger.handlers:
        if hasattr(handler, "flush"):
            handler.flush()

    # ログファイルが生成され、内容にメッセージが含まれることを確認する。
    assert log_file.exists()
    assert "テストメッセージ" in log_file.read_text(encoding="utf-8")

    # テスト間の副作用を防ぐためにハンドラをクリーンアップする。
    _cleanup_logger_handlers("my_editor")


def test_setup_logging_rejects_invalid_retention(tmp_path: Path) -> None:
    """不正な保持日数を指定した場合に例外が発生することを検証する。

    Args:
        tmp_path (Path): Pytestの一時ディレクトリ。
    """
    # 不正な保持日数を設定して関数を実行する。
    with pytest.raises(ValueError) as exc_info:
        setup_logging(log_path=tmp_path / "invalid.log", retention_days=0)

    # エラーメッセージが期待通りであることを確認する。
    assert "保持日数は0より大きく" in str(exc_info.value)

    # 副作用を防ぐためにロガーハンドラを後処理する。
    _cleanup_logger_handlers("my_editor")
