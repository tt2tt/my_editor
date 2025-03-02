import sys
import os
import pytest

from PySide6.QtWidgets import QApplication

# プロジェクトのルートディレクトリをsys.pathに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    editor = FileEditor()
    qtbot.addWidget(editor)
    return editor

def test_zoom_in(app, qtbot):
    """拡大機能のテスト"""
    initial_font_size = app.font().pointSize()
    app.zoom_in()
    new_font_size = app.font().pointSize()
    assert new_font_size > initial_font_size

def test_zoom_out(app, qtbot):
    """縮小機能のテスト"""
    initial_font_size = app.font().pointSize()
    app.zoom_out()
    new_font_size = app.font().pointSize()
    assert new_font_size < initial_font_size
