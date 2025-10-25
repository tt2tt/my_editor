from __future__ import annotations

from typing import Any, Dict, List

import pytest

from controllers.event_bus import EventBus


def test_publish_triggers_handler() -> None:
    """publishが購読済みハンドラを呼び出すことを検証する。"""
    # イベントバスを生成し、呼び出し結果を格納するリストを用意する。
    bus = EventBus()
    received: List[Dict[str, Any] | None] = []

    # テスト用ハンドラを登録する。
    def handler(payload: Dict[str, Any] | None) -> None:
        received.append(payload)

    bus.subscribe("sample", handler)

    # イベントを発行してハンドラが動作するか確認する。
    payload = {"value": 42}
    bus.publish("sample", payload)

    # ハンドラが1回だけ呼ばれ、ペイロードが渡されたことを検証する。
    assert received == [payload]


def test_publish_handles_missing_subscribers(caplog: pytest.LogCaptureFixture) -> None:
    """購読者がいないイベントをpublishしてもエラーにならないことを確認する。"""
    # イベントバスを生成し、デバッグログを捕捉する準備を行う。
    caplog.set_level("DEBUG")
    bus = EventBus()

    # 購読者がいないイベントを発行する。
    bus.publish("no_listeners")

    # 例外が発生しないことと、情報がログに残ることを検証する。
    assert caplog.records  # ログ出力が行われたことを確認する。
    assert any("登録されたハンドラはありません" in record.message for record in caplog.records)
