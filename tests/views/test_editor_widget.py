from __future__ import annotations

from collections.abc import Generator
from typing import cast

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication

from views.editor_widget import EditorWidget


@pytest.fixture(name="qt_app")
def fixture_qt_app() -> Generator[QApplication, None, None]:
    """テスト全体で共有するQApplicationインスタンスを管理する。"""
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    yield cast(QApplication, app_instance)


def test_wheel_event_zoom(qt_app: QApplication) -> None:
    """Ctrl+ホイール操作でズームレベルが変化することを検証する。"""
    widget = EditorWidget()
    initial_zoom = widget.current_zoom_level

    zoom_in_event = QWheelEvent(
        QPointF(0, 0),
        QPointF(0, 0),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.ControlModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
        Qt.MouseEventSource.MouseEventNotSynthesized,
    )
    widget.wheelEvent(zoom_in_event)

    assert widget.current_zoom_level == initial_zoom + 1

    zoom_out_event = QWheelEvent(
        QPointF(0, 0),
        QPointF(0, 0),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.ControlModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
        Qt.MouseEventSource.MouseEventNotSynthesized,
    )
    widget.wheelEvent(zoom_out_event)

    assert widget.current_zoom_level == initial_zoom

    no_mod_event = QWheelEvent(
        QPointF(0, 0),
        QPointF(0, 0),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
        Qt.MouseEventSource.MouseEventNotSynthesized,
    )
    widget.wheelEvent(no_mod_event)

    assert widget.current_zoom_level == initial_zoom

    qt_app.processEvents()