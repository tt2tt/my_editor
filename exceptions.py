from __future__ import annotations

from typing import Optional


class EditorError(Exception):
    """アプリ共通の例外基底クラス。"""


class FileOperationError(EditorError):
    """ファイル入出力に関する例外。"""


class AIIntegrationError(EditorError):
    """AI連携に起因する例外。"""


def raise_with_context(message: str, original: Optional[Exception] = None) -> None:
    """受け取った例外に文脈を付与して再送出する。

    Args:
        message (str): 例外に付与する説明メッセージ。
        original (Optional[Exception]): 元となる例外。省略可。

    Raises:
        EditorError: 文脈付きの例外を送出する。
    """
    # 文脈付きの例外を構築する。
    error = EditorError(message)

    # 元例外が渡された場合はチェーンして情報を保持する。
    if original is not None:
        raise error from original

    # 元例外が無い場合は単純に送出する。
    raise error
