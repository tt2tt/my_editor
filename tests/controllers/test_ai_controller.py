from __future__ import annotations

from typing import Generator, Iterable

import pytest

from controllers.ai_controller import AIController, AIClientProtocol
from exceptions import AIIntegrationError


class _StubClient(AIClientProtocol):
    """テスト用のスタブクライアント。"""

    def __init__(self, *, response: str = "", stream_chunks: Iterable[str] | None = None, should_fail: bool = False) -> None:
        self._response = response
        self._stream_chunks = list(stream_chunks or [])
        self._should_fail = should_fail
        self.last_prompt: str | None = None

    def generate(self, model: str, prompt: str) -> str:
        if self._should_fail:
            raise RuntimeError("stub failure")
        self.last_prompt = prompt
        return f"{model}:{prompt}:{self._response}" if self._response else f"{model}:{prompt}"

    def stream(self, model: str, prompt: str) -> Iterable[str]:
        if self._should_fail:
            raise RuntimeError("stream failure")
        if self._stream_chunks:
            return iter(self._stream_chunks)
        return iter([f"{model}:{prompt}"])


def test_handle_chat_submit_returns_response() -> None:
    """handle_chat_submitが応答文字列を返すことを検証する。"""
    client = _StubClient(response="ok")
    controller = AIController(client=client)

    result = controller.handle_chat_submit(" hello ")

    assert result.endswith("ok")
    assert client.last_prompt == "hello"


def test_handle_chat_submit_raises_on_empty() -> None:
    """空文字列を送信した場合に例外が発生することを検証する。"""
    controller = AIController(client=_StubClient())

    with pytest.raises(ValueError):
        controller.handle_chat_submit("  \n  ")


def test_handle_chat_submit_wraps_errors() -> None:
    """下層例外がAIIntegrationErrorへ変換されることを検証する。"""
    controller = AIController(client=_StubClient(should_fail=True))

    with pytest.raises(AIIntegrationError):
        controller.handle_chat_submit("prompt")


def test_generate_code_handles_error() -> None:
    """下層処理の失敗がAIIntegrationErrorに変換されることを検証する。"""
    controller = AIController(client=_StubClient(should_fail=True))

    with pytest.raises(AIIntegrationError):
        controller.generate_code("test prompt")


def test_generate_code_returns_text() -> None:
    """generate_codeがレスポンス文字列を返却することを検証する。"""
    controller = AIController(client=_StubClient(response="ok"))

    result = controller.generate_code("prompt")

    assert result.endswith("ok")


def test_stream_chat_yields_chunks() -> None:
    """stream_chatがチャンクを逐次返却することを検証する。"""
    controller = AIController(client=_StubClient(stream_chunks=["a", "b", "c"]))

    chunks = list(controller.stream_chat("prompt"))

    assert chunks == ["a", "b", "c"]