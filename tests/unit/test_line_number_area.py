import pytest
from PySide6.QtWidgets import QApplication

from my_package.line_number_area import LineNumberArea
from my_package.editor import FileEditor

@pytest.fixture(scope="session")
def app():
    """QApplicationのインスタンスを作成するフィクスチャ"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def file_editor(app):
    """FileEditorのインスタンスを作成するフィクスチャ"""
    editor = FileEditor()
    return editor

@pytest.fixture
def line_number_area(file_editor):
    """LineNumberAreaのインスタンスを作成するフィクスチャ"""
    return LineNumberArea(file_editor)

def test_size_hint(line_number_area):
    """LineNumberAreaのサイズヒントのテスト"""
    size_hint = line_number_area.sizeHint()
    assert size_hint.width() > 0
    assert size_hint.height() == 0

def test_paint_event(line_number_area, mocker):
    """LineNumberAreaの描画イベントのテスト"""
    mock_paint_event = mocker.patch.object(line_number_area.editor, 'line_number_area_paint_event')
    event = mocker.Mock()
    line_number_area.paintEvent(event)
    mock_paint_event.assert_called_once_with(event)
