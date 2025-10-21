from __future__ import annotations

import pytest

from exceptions import AIIntegrationError, EditorError, FileOperationError, raise_with_context


def test_exception_hierarchy() -> None:
    """例外クラスがEditorErrorを継承していることを検証する。"""
    # 各例外が期待する継承関係を持つことを確認する。
    assert issubclass(FileOperationError, EditorError)
    assert issubclass(AIIntegrationError, EditorError)


def test_raise_with_context_wraps_exception() -> None:
    """元例外をチェーンして再送出することを検証する。"""
    # 送出される例外とチェーンが正しいことを確認する。
    original = ValueError("元エラー")
    with pytest.raises(EditorError) as exc_info:
        raise_with_context("ラップされたエラー", original)

    # cause属性に元例外が設定されることを確認する。
    assert exc_info.value.__cause__ is original


def test_raise_with_context_without_original() -> None:
    """元例外なしでもEditorErrorが送出されることを検証する。"""
    # 元例外が無い場合でもメッセージ付きで送出されることを確認する。
    with pytest.raises(EditorError) as exc_info:
        raise_with_context("単独のエラー")

    # メッセージ内容が維持されることを確認する。
    assert str(exc_info.value) == "単独のエラー"
    # causeがNoneであることを確認する。
    assert exc_info.value.__cause__ is None
