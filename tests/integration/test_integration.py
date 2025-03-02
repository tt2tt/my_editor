import pytest
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtGui import QTextCursor
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
    window.show()
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

# 追加: Ctrl+Sショートカットの統合テスト
def test_ctrl_s_shortcut_saves_file_integration(main_window, mocker):
    """MainWindowでのCtrl+Sショートカットがファイル保存をトリガーする統合テスト"""
    main_window.new_file()
    main_window.activateWindow()
    main_window.setFocus()
    mocker.patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=("test_save.txt", ""))
    current_editor = main_window.tab_manager.currentWidget()
    save_mock = mocker.patch.object(current_editor, 'save_file')
    # 登録されているCtrl+Sショートカットのアクションを直接トリガーする
    for action in main_window.actions():
        if action.shortcut().toString() == "Ctrl+S":
            action.trigger()
            break
    QTest.qWait(100)  # イベント処理の待機
    save_mock.assert_called_once_with("test_save.txt")

def test_search_literal_integration(main_window):
    """MainWindowでのリテラル検索の統合テスト"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    editor.setPlainText("Integration test for literal search functionality.")
    # Reset cursor and search attributes
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    main_window.regex_checkbox.setChecked(False)
    main_window.search_box.setText("literal")
    main_window.search_text()
    cursor = editor.textCursor()
    selected = cursor.selectedText()
    assert "literal" in selected

def test_search_regex_integration(main_window):
    """MainWindowでの正規表現検索の統合テスト"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    editor.setPlainText("Integration test for regex search functionality.")
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    main_window.regex_checkbox.setChecked(True)
    main_window.search_box.setText("r.*x")
    main_window.search_text()
    cursor = editor.textCursor()
    selected = cursor.selectedText()
    # "regex" should be matched by pattern r.*x
    assert "regex" in selected

def test_search_not_found_integration(main_window):
    """MainWindowでの検索機能（検索対象が見つからない場合）の統合テスト"""
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

def test_replace_integration(main_window):
    """MainWindowでの置換機能の統合テスト（部分置換）"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    # 初期テキストを設定
    editor.setPlainText("Integration test: Hello world! This is a test.")
    # 検索と選択
    main_window.regex_checkbox.setChecked(False)
    main_window.search_box.setText("world")
    main_window.search_text()
    # 置換操作（現在選択中を置換）
    main_window.replace_box.setText("universe")
    main_window.replace_text()
    new_text = editor.toPlainText()
    # "world" が "universe" に置き換わっているはず
    assert "universe" in new_text and "world" not in new_text

def test_replace_all_integration(main_window):
    """MainWindowでの全置換機能の統合テスト"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    # 複数箇所に同じ単語があるテキストを設定
    editor.setPlainText("Integration test: Hello world! Hello world!")
    # リテラル置換モードで全置換を実行
    main_window.regex_checkbox.setChecked(False)
    main_window.search_box.setText("world")
    main_window.replace_box.setText("universe")
    main_window.replace_all_text()
    new_text = editor.toPlainText()
    assert new_text == "Integration test: Hello universe! Hello universe!"

def test_redo_edit_integration(main_window):
    """MainWindowでのRedo機能の統合テスト"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    initial_text = "Hello"
    editor.setPlainText(initial_text)
    
    # 変更：テキストを追加して変更
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.End)
    editor.setTextCursor(cursor)
    editor.insertPlainText(" world")
    updated_text = editor.toPlainText()
    
    # Undo → Redo の動作確認
    main_window.undo_edit()
    assert editor.toPlainText() == initial_text
    
    main_window.redo_edit()
    assert editor.toPlainText() == updated_text

def test_save_file_updates_tab_name_integration(main_window, mocker):
    """新規ファイル保存時にタブ名が保存したファイル名に更新されるかの統合テスト"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    test_path = "c:/Users/grove/OneDrive/Desktop/開発/my_editor/test_save_name_integration.txt"
    mocker.patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=(test_path, ""))
    # 実際のファイル書き込みを行わないためのダミーsave_file
    editor.save_file = lambda f: setattr(editor, 'current_file', f)
    main_window.save_file()
    index = main_window.tab_manager.indexOf(editor)
    expected_name = os.path.basename(test_path)
    assert main_window.tab_manager.tabText(index) == expected_name

def test_open_folder_integration(main_window, mocker):
    """MainWindowでフォルダを開く統合テスト：新規タブにQSplitterが追加され、ツリーが存在することを確認"""
    dummy_folder = "c:/dummy_integration_folder"
    mocker.patch('PySide6.QtWidgets.QFileDialog.getExistingDirectory', return_value=dummy_folder)
    initial_count = main_window.tab_manager.count()
    main_window.open_folder()
    new_count = main_window.tab_manager.count()
    assert new_count == initial_count + 1
    from PySide6.QtWidgets import QSplitter, QTreeView
    widget = main_window.tab_manager.currentWidget()
    assert isinstance(widget, QSplitter)
    # QTreeViewが含まれているか検証
    tree_views = widget.findChildren(QTreeView)
    assert len(tree_views) > 0
