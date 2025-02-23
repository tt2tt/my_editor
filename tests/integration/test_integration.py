import pytest
import sys
import os
from PySide6.QtWidgets import QApplication
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from main_window import MainWindow
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
def main_window(app):
    """MainWindowのインスタンスを作成するフィクスチャ"""
    window = MainWindow()
    return window

def test_add_tab_in_main_window(main_window):
    """MainWindowでタブを追加するテスト"""
    initial_count = main_window.tab_manager.count()
    main_window.tab_manager.add_new_tab("テストタブ", FileEditor())
    assert main_window.tab_manager.count() == initial_count + 1
    assert main_window.tab_manager.tabText(initial_count) == "テストタブ"

def test_remove_tab_in_main_window(main_window):
    """MainWindowでタブを削除するテスト"""
    main_window.tab_manager.add_new_tab("削除タブ", FileEditor())
    initial_count = main_window.tab_manager.count()
    main_window.tab_manager.remove_tab(initial_count - 1)
    assert main_window.tab_manager.count() == initial_count - 1

def test_open_file_in_main_window(main_window, mocker):
    """MainWindowでファイルを開くテスト"""
    mocker.patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=("test.txt", ""))
    mocker.patch('my_package.editor.FileEditor.open_file')
    main_window.open_file()
    assert main_window.tab_manager.count() == 2  # デフォルトタブ + 新しいタブ

def test_save_file_in_main_window(main_window, mocker):
    """MainWindowでファイルを保存するテスト"""
    mocker.patch('my_package.editor.FileEditor.save_file')
    main_window.save_file()
    current_widget = main_window.tab_manager.currentWidget()
    if isinstance(current_widget, FileEditor):
        current_widget.save_file.assert_called_once()
