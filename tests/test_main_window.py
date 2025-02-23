import sys
import os
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QWheelEvent

# プロジェクトのルートディレクトリをsys.pathに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'my_editor')))

from main_window import MainWindow
from my_package.editor import FileEditor

@pytest.fixture(scope="session")
def qapp():
    """QApplicationのインスタンスを作成するフィクスチャ"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def app(qtbot, qapp):
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def simulate_wheel_event(widget, delta):
    """ホイールイベントをシミュレートする"""
    event = QWheelEvent(widget.rect().center(), widget.mapToGlobal(widget.rect().center()), 
                        QPoint(0, delta), QPoint(0, delta), Qt.NoButton, Qt.ControlModifier, 
                        Qt.NoScrollPhase, False)
    QApplication.sendEvent(widget, event)

def test_zoom_in(app, qtbot):
    """拡大機能のテスト"""
    editor = FileEditor()
    app.tab_manager.add_new_tab("テストタブ", editor)
    initial_font_size = editor.font().pointSize()
    qtbot.keyPress(app, Qt.Key_Control)
    simulate_wheel_event(app, 120)  # 120はホイールの1ステップ
    qtbot.keyRelease(app, Qt.Key_Control)
    new_font_size = editor.font().pointSize()
    assert new_font_size > initial_font_size

def test_zoom_out(app, qtbot):
    """縮小機能のテスト"""
    editor = FileEditor()
    app.tab_manager.add_new_tab("テストタブ", editor)
    initial_font_size = editor.font().pointSize()
    qtbot.keyPress(app, Qt.Key_Control)
    simulate_wheel_event(app, -120)  # -120はホイールの1ステップ
    qtbot.keyRelease(app, Qt.Key_Control)
    new_font_size = editor.font().pointSize()
    assert new_font_size < initial_font_size
