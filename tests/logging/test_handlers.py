from __future__ import annotations

import io
import logging
from typing import Any

import pytest

from app_logging.handlers import attach_gui_handler, log_user_action


class DummyStatusBar:
    """メッセージ表示を記録するテスト用ステータスバー。"""

    def __init__(self) -> None:
        self.messages: list[tuple[str, int]] = []

    def showMessage(self, message: str, timeout: int = 0) -> None:  # noqa: N802
        self.messages.append((message, timeout))


class DummyWindow:
    """statusBarメソッドのみを持つテスト用ウィンドウ。"""

    def __init__(self, status_bar: DummyStatusBar) -> None:
        self._status_bar = status_bar

    def statusBar(self) -> DummyStatusBar:  # noqa: N802
        return self._status_bar


def _clear_logger(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.propagate = True


def test_attach_gui_handler_emits_to_status_bar() -> None:
    status_bar = DummyStatusBar()
    window = DummyWindow(status_bar)

    logger = logging.getLogger("my_editor")
    _clear_logger(logger)

    handler = attach_gui_handler(window, timeout_ms=3000)
    try:
        logger.info("テストメッセージ")
    finally:
        logger.removeHandler(handler)
        handler.close()

    assert status_bar.messages
    message, timeout = status_bar.messages[-1]
    assert "テストメッセージ" in message
    assert timeout == 3000


def test_log_user_action_outputs_structured_json() -> None:
    logger = logging.getLogger("my_editor.user_action")
    _clear_logger(logger)

    stream = io.StringIO()
    stream_handler = logging.StreamHandler(stream)
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    try:
        log_user_action("open_file", {"path": "sample.py", "success": True})
        stream_handler.flush()
        output = stream.getvalue().strip()
    finally:
        logger.removeHandler(stream_handler)
        stream_handler.close()

    assert '"action": "open_file"' in output
    assert '"path": "sample.py"' in output
    assert '"success": true' in output
