from __future__ import annotations

import json
import logging
from typing import Any, Mapping, Optional


class _StatusBarHandler(logging.Handler):
    """Qtのステータスバーへログメッセージを転送するハンドラ。"""

    def __init__(self, status_bar: Any, timeout_ms: int = 5000) -> None:
        super().__init__(level=logging.INFO)
        self._status_bar = status_bar
        self._timeout_ms = timeout_ms

    def emit(self, record: logging.LogRecord) -> None:
        """ログレコードを受け取りステータスバーへ表示する。"""
        message = self.format(record)
        try:
            self._status_bar.showMessage(message, self._timeout_ms)
        except Exception:  # noqa: BLE001
            logging.getLogger("my_editor").debug(
                "ステータスバーへのログ表示に失敗しました。", exc_info=True
            )


def attach_gui_handler(window: Any, *, timeout_ms: int = 5000) -> logging.Handler:
    """GUIウィンドウにログ表示ハンドラをアタッチする。"""
    if window is None:
        raise ValueError("ウィンドウが指定されていません。")

    status_bar_getter = getattr(window, "statusBar", None)
    if not callable(status_bar_getter):
        raise ValueError("ウィンドウにstatusBarメソッドが存在しません。")

    status_bar = status_bar_getter()
    if status_bar is None:
        raise ValueError("statusBar() が None を返しました。")

    handler = _StatusBarHandler(status_bar=status_bar, timeout_ms=timeout_ms)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    logger = logging.getLogger("my_editor")
    if logger.level > logging.INFO or logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return handler


def log_user_action(action: str, detail: Optional[Mapping[str, Any]] = None) -> None:
    """ユーザー操作をJSON形式でロギングする。"""
    if not action:
        raise ValueError("action を指定してください。")

    payload = {
        "action": action,
        "detail": dict(detail) if detail is not None else {},
    }
    message = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    logger = logging.getLogger("my_editor.user_action")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(stream_handler)
        logger.propagate = False

    logger.info(message)
