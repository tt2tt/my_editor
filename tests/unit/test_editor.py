import pytest
from PySide6.QtWidgets import QApplication
from my_package.editor import FileEditor
import os

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

def test_open_file(file_editor, tmp_path):
    """ファイルを開くテスト"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!", encoding='utf-8')

    file_editor.open_file(str(test_file))
    assert file_editor.toPlainText() == "Hello, world!"
    assert file_editor.current_file == str(test_file)

def test_save_file(file_editor, tmp_path):
    """ファイルを保存するテスト"""
    test_file = tmp_path / "test.txt"
    file_editor.setPlainText("Hello, world!")
    file_editor.save_file(str(test_file))

    assert test_file.read_text(encoding='utf-8') == "Hello, world!"
    assert file_editor.current_file == str(test_file)
