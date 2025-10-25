from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List

Payload = Dict[str, Any] | None
Handler = Callable[[Payload], None]


class EventBus:
    """アプリ内コンポーネント間の通知を仲介する簡易イベントバス。"""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """購読情報とロガーを初期化する。

        Args:
            logger (logging.Logger | None): ログ出力に使用するロガー。省略時は`my_editor`ロガー。
        """
        # ロガーを保持し、購読者リストの辞書を整備する。
        self._logger = logger or logging.getLogger("my_editor")
        self._subscriptions: Dict[str, List[Handler]] = {}

    def subscribe(self, event: str, handler: Handler) -> None:
        """イベントに対してハンドラを登録する。

        Args:
            event (str): 購読対象のイベント名。
            handler (Handler): イベント受信時に実行するコールバック。
        """
        # イベントごとのリストを取得し、二重登録を避けつつ追加する。
        handlers = self._subscriptions.setdefault(event, [])
        if handler not in handlers:
            handlers.append(handler)
            self._logger.debug("イベント'%s'にハンドラを登録しました。", event)

    def publish(self, event: str, payload: Payload = None) -> None:
        """イベントを発行して登録済みハンドラへ通知する。

        Args:
            event (str): 発行するイベント名。
            payload (Payload): ハンドラへ渡すデータ。省略時はNone。
        """
        # ハンドラが存在しない場合は何もせず終了する。
        handlers = self._subscriptions.get(event, [])
        if not handlers:
            self._logger.debug("イベント'%s'に登録されたハンドラはありません。", event)
            return

        # ハンドラをコピーし、例外発生時も後続が実行されるよう保護する。
        for handler in list(handlers):
            try:
                handler(payload)
            except Exception:  # noqa: BLE001
                self._logger.exception("イベント'%s'のハンドラ実行中に例外が発生しました。", event)
