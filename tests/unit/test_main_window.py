import pytest
from PySide6.QtWidgets import QApplication, QMenu
from main_window import MainWindow
from my_package.editor import FileEditor
from PySide6.QtGui import QTextCursor

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

def test_window_title(main_window):
    """ウィンドウタイトルのテスト"""
    assert main_window.windowTitle() == "マイエディタ"

def test_window_geometry(main_window):
    """ウィンドウのジオメトリのテスト"""
    geom = main_window.geometry()
    assert geom.x() == 100
    assert geom.y() == 100
    assert geom.width() == 800
    assert geom.height() == 600

def test_menu_bar_exists(main_window):
    """メニューバーが存在するかのテスト"""
    menu_bar = main_window.menuBar()
    assert menu_bar is not None

def test_file_menu_exists(main_window):
    """ファイルメニューが存在するかのテスト"""
    menu_bar = main_window.menuBar()
    file_menu = None
    for action in menu_bar.actions():
        if action.menu() and action.text() == "&ファイル":
            file_menu = action.menu()
            break
    assert file_menu is not None

def test_file_menu_actions(main_window):
    """ファイルメニューのアクションのテスト"""
    menu_bar = main_window.menuBar()
    file_menu = None
    for action in menu_bar.actions():
        if action.menu() and action.text() == "&ファイル":
            file_menu = action.menu()
            break
    assert file_menu is not None
    actions = [action.text() for action in file_menu.actions()]
    assert "&新しいファイル" in actions
    assert "&ファイルを開く" in actions
    assert "&保存" in actions
    assert "&終了" in actions

def test_open_file_action(main_window, mocker):
    """ファイルを開くアクションのテスト"""
    mocker.patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=("test.txt", ""))
    mocker.patch('my_package.editor.FileEditor.open_file')
    main_window.open_file()
    assert main_window.tab_manager.count() == 1

def test_new_file_action(main_window):
    """新しいファイルを作成するアクションのテスト"""
    main_window.new_file()
    assert main_window.tab_manager.count() == 1

def test_save_file_action(main_window, mocker):
    """ファイルを保存するアクションのテスト"""
    mocker.patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=("test_save.txt", ""))
    mocker.patch('my_package.editor.FileEditor.save_file')
    main_window.new_file()
    main_window.save_file()
    current_widget = main_window.tab_manager.currentWidget()
    if isinstance(current_widget, FileEditor):
        current_widget.save_file.assert_called_once_with("test_save.txt")

def test_search_literal_found(main_window):
    """リテラル検索テスト（対象が見つかる場合）"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    editor.setPlainText("Hello world! This is a test.")
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    
    # リテラル検索：正規表現チェックをオフ
    if main_window.regex_checkbox.isChecked():
        main_window.regex_checkbox.setChecked(False)
    main_window.search_box.setText("world")
    main_window.search_text()
    
    cursor = editor.textCursor()
    selected = cursor.selectedText()
    assert "world" in selected

def test_search_literal_not_found(main_window):
    """リテラル検索テスト（対象が見つからない場合）"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    editor.setPlainText("Hello world! This is a test.")
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    
    initial_pos = editor.textCursor().position()
    if main_window.regex_checkbox.isChecked():
        main_window.regex_checkbox.setChecked(False)
    main_window.search_box.setText("nonexistent")
    main_window.search_text()
    
    final_pos = editor.textCursor().position()
    assert final_pos == initial_pos

def test_search_regex_found(main_window):
    """正規表現検索テスト（対象が見つかる場合）"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    editor.setPlainText("Hello world! This is a test.")
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    
    main_window.regex_checkbox.setChecked(True)
    main_window.search_box.setText("w.*d")
    main_window.search_text()
    
    cursor = editor.textCursor()
    selected = cursor.selectedText()
    # w.*d should match "world"
    assert "world" in selected

def test_search_regex_invalid(main_window):
    """正規表現検索テスト（無効な正規表現の場合）"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    editor.setPlainText("Hello world! This is a test.")
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    
    main_window.regex_checkbox.setChecked(True)
    main_window.search_box.setText("*invalid")
    current_pos_before = editor.textCursor().position()
    main_window.search_text()
    current_pos_after = editor.textCursor().position()
    # 検索できなければカーソル位置は変わらない
    assert current_pos_after == current_pos_before

def test_replace_text(main_window):
    """置換テスト（現在の選択部分を置換する）"""
    # 新しいファイルを作成し、内容を設定
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    editor.setPlainText("Hello world! This is a test.")
    # 検索: "world" を選択
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    if main_window.regex_checkbox.isChecked():
        main_window.regex_checkbox.setChecked(False)
    main_window.search_box.setText("world")
    main_window.search_text()
    # 置換: "world" -> "universe"
    main_window.replace_box.setText("universe")
    main_window.replace_text()
    # 置換後、選択部分に "universe" が含まれるはず
    cursor = editor.textCursor()
    selected = cursor.selectedText()
    assert "universe" in selected or "universe" in editor.toPlainText()

def test_replace_all_text(main_window):
    """全置換テスト：全ての検索対象を置換欄の内容で置換する"""
    main_window.new_file()
    editor = main_window.tab_manager.currentWidget()
    # 複数箇所に "world" を配置
    editor.setPlainText("Hello world! Hello world!")
    # リテラル検索モード
    if main_window.regex_checkbox.isChecked():
        main_window.regex_checkbox.setChecked(False)
    main_window.search_box.setText("world")
    main_window.replace_box.setText("universe")
    main_window.replace_all_text()
    new_text = editor.toPlainText()
    # 全置換されていることを確認
    assert new_text == "Hello universe! Hello universe!"