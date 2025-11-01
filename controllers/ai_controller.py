from __future__ import annotations

import logging
from typing import Any, Iterable, Iterator, Optional, Protocol

from exceptions import AIIntegrationError
from settings.model import SettingsModel


class AIClientProtocol(Protocol):
    """AIクライアントの最小インターフェース。"""

    def generate(self, model: str, prompt: str) -> str:
        """単一応答を同期的に生成する。"""

    def stream(self, model: str, prompt: str) -> Iterable[str]:
        """ストリーム形式で応答を生成する。"""


class AIController:
    """OpenAI連携によるコード生成やチャット応答を提供するコントローラ。"""

    def __init__(
        self,
        client: Optional[AIClientProtocol] = None,
        *,
        model: str = "gpt-4o-mini",
        logger: Optional[logging.Logger] = None,
        settings_model: Optional[SettingsModel] = None,
    ) -> None:
        """コントローラの依存を初期化する。"""
        self._logger = logger or logging.getLogger("my_editor.ai_controller")
        self._settings_model = settings_model
        self._client: Optional[AIClientProtocol] = client
        self._client_provided = client is not None
        self._model = model

    def generate_code(self, prompt: str) -> str:
        """コード生成リクエストを実行し、結果文字列を返す。"""
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("プロンプトが空です。")

        self._logger.info("コード生成リクエストを送信します。")
        try:
            result = self._get_client().generate(self._model, prompt)
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("コード生成に失敗しました。", exc_info=exc)
            raise AIIntegrationError("コード生成に失敗しました。") from exc

        self._logger.info("コード生成が完了しました。")
        return result

    def stream_chat(self, prompt: str) -> Iterator[str]:
        """チャット応答をストリームで取得する。"""
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("プロンプトが空です。")

        self._logger.info("チャットストリームを開始します。")
        try:
            for chunk in self._get_client().stream(self._model, prompt):
                if chunk:
                    yield chunk
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("チャットストリームに失敗しました。", exc_info=exc)
            raise AIIntegrationError("チャットストリームに失敗しました。") from exc

        self._logger.info("チャットストリームが終了しました。")

    def handle_chat_submit(self, message: str) -> str:
        """チャットメッセージを送信して応答を取得する。"""
        normalized = message.strip()
        if not normalized:
            raise ValueError("メッセージが空です。")

        self._logger.info("チャット補完リクエストを送信します。")
        try:
            response = self._get_client().generate(self._model, normalized)
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("チャット応答の生成に失敗しました。", exc_info=exc)
            raise AIIntegrationError("チャット応答の生成に失敗しました。") from exc

        self._logger.info("チャット応答を受信しました。")
        return response

    def reset_client(self) -> None:
        """内部で保持しているクライアントを再生成できるようリセットする。"""
        if self._client_provided:
            self._logger.debug("外部提供のクライアントはリセット対象外です。")
            return
        self._client = None

    def _get_client(self) -> AIClientProtocol:
        """利用可能なAIクライアントを取得する。"""
        if self._client is None:
            self._client = self._build_default_client()
        return self._client

    def _build_default_client(self) -> AIClientProtocol:
        """設定モデルからAPIキーを読み取りクライアントを生成する。"""
        if self._settings_model is None:
            raise AIIntegrationError("設定モデルが提供されていません。")

        try:
            api_key = self._settings_model.get_api_key()
        except Exception as exc:  # noqa: BLE001
            self._logger.error("APIキーの取得に失敗しました。", exc_info=exc)
            raise AIIntegrationError("APIキーの取得に失敗しました。") from exc

        if not api_key:
            raise AIIntegrationError("OpenAI APIキーが設定されていません。")

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - 実運用依存
            raise AIIntegrationError("openaiパッケージがインストールされていません。") from exc

        return _OpenAIClientAdapter(OpenAI(api_key=api_key))


class _OpenAIClientAdapter:
    """OpenAI公式クライアントをAIClientProtocolに適合させる。"""

    def __init__(self, client: Any) -> None:
        self._client: Any = client

    def generate(self, model: str, prompt: str) -> str:
        response = self._client.responses.create(model=model, input=prompt)
        return _extract_text(response)

    def stream(self, model: str, prompt: str) -> Iterable[str]:
        stream = self._client.responses.stream(model=model, input=prompt)
        try:
            for event in stream:
                text = _extract_stream_text(event)
                if text:
                    yield text
        finally:
            close = getattr(stream, "close", None)
            if callable(close):
                close()


def _extract_text(response: object) -> str:
    """OpenAIレスポンスからテキストを抽出する。"""
    if isinstance(response, str):
        return response

    if isinstance(response, dict):
        return _extract_text_from_content(response)

    output = getattr(response, "output", None) or getattr(response, "outputs", None)
    if isinstance(output, list):
        return "".join(_extract_text_from_content(item) for item in output)

    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text

    content = getattr(response, "content", None) or getattr(response, "contents", None)
    if isinstance(content, list):
        return "".join(_extract_text_from_content(item) for item in content)

    return str(response)


def _extract_text_from_content(data: object) -> str:
    """辞書もしくはオブジェクトからテキストを抽出する。"""
    if isinstance(data, str):
        return data

    if isinstance(data, dict):
        segments: list[str] = []
        text = data.get("text")
        if isinstance(text, str):
            segments.append(text)
        content = data.get("content") or data.get("contents")
        if isinstance(content, list):
            for entry in content:
                extracted = _extract_text_from_content(entry)
                if extracted:
                    segments.append(extracted)
        return "".join(segments)

    text_attr = getattr(data, "text", None)
    if isinstance(text_attr, str):
        return text_attr

    content_attr = getattr(data, "content", None) or getattr(data, "contents", None)
    if isinstance(content_attr, list):
        return "".join(_extract_text_from_content(entry) for entry in content_attr)

    return str(data)


def _extract_stream_text(event: object) -> str:
    """OpenAIストリーミングイベントからテキストを抽出する。"""
    if isinstance(event, str):
        return event
    if isinstance(event, dict):
        delta = event.get("delta") or {}
        if isinstance(delta, dict):
            text = delta.get("text")
            if text:
                return str(text)
        text = event.get("text")
        if text:
            return str(text)
        return ""

    event_type = getattr(event, "type", "")
    if event_type and event_type.endswith("delta"):
        delta = getattr(event, "delta", None)
        if isinstance(delta, dict):
            text = delta.get("text")
            if text:
                return str(text)
    text = getattr(event, "text", None)
    if text:
        return str(text)
    return ""
