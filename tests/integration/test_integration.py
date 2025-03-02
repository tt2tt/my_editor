import pytest
import sys
import os
from PySide6.QtWidgets import QApplication
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from main_window import MainWindow
from my_package.editor import FileEditor
from my_package.line_number_area import LineNumberArea

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
    assert main_window.tab_manager.count() == 1

def test_save_file_in_main_window(main_window, mocker):
    """MainWindowでファイルを保存するテスト"""
    mocker.patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=("test_save.txt", ""))
    mocker.patch('my_package.editor.FileEditor.save_file')
    main_window.new_file()
    main_window.save_file()
    current_widget = main_window.tab_manager.currentWidget()
    if isinstance(current_widget, FileEditor):
        current_widget.save_file.assert_called_once_with("test_save.txt")

def test_search_function_integration(main_window):
    """MainWindowでの検索機能の統合テスト"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    editor.setPlainText("Integration test for search functionality.")
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    
    main_window.search_box.setText("search")
    main_window.search_text()
    
    cursor = editor.textCursor()
    selected = cursor.selectedText()
    assert "search" in selected

def test_search_function_not_found_integration(main_window):
    """MainWindowでの検索機能の統合テスト（検索対象が見つからない場合）"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    editor.setPlainText("Integration test for search functionality.")
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    
    initial_position = editor.textCursor().position()
    
    main_window.search_box.setText("nonexistent")
    main_window.search_text()
    
    final_position = editor.textCursor().position()
    assert final_position == initial_position
