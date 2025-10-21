from __future__ import annotations

import logging
from logging import Logger
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

DEFAULT_RETENTION_DAYS = 30


def setup_logging(log_path: Path, retention_days: int = DEFAULT_RETENTION_DAYS) -> Logger:
    """指定されたパスで日次ローテーション付きのロガーを構築する。

    Args:
        log_path (Path): ログを書き出すファイルパス。
        retention_days (int): 保持するログファイル数。デフォルトは30日分。

    Returns:
        Logger: 設定済みのアプリケーションロガー。

    Raises:
        ValueError: retention_days が正の値でない場合。
    """
    # ログ保持日数を検証する。
    if retention_days <= 0:
        raise ValueError("保持日数は0より大きくなければなりません。")

    # ログファイルパスをPath化し、ディレクトリを準備する。
    resolved_path = Path(log_path).expanduser().resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    # アプリケーションロガーを取得し、重複ハンドラを防ぐために初期化する。
    logger = logging.getLogger("my_editor")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # 既存ハンドラを除去してリフレッシュする。
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    # 日次ローテーションするファイルハンドラを準備する。
    file_handler = TimedRotatingFileHandler(
        filename=str(resolved_path),
        when="midnight",
        interval=1,
        backupCount=retention_days,
        encoding="utf-8",
        utc=False,
    )
    file_handler.setLevel(logging.INFO)

    # ログメッセージのフォーマットを設定する。
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    # ファイルハンドラをロガーへ追加する。
    logger.addHandler(file_handler)

    # コンソール出力を追加してデバッグしやすくする。
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
