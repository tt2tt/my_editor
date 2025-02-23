import pytest
from PySide6.QtWidgets import QApplication, QMenu
from main_window import MainWindow
from my_package.editor import FileEditor

@pytest.fixture(scope="session")
def app():
    """QApplicationのインスタンスを作成するフィクスチャ"""
    app = QApplication.instance()
    if (app is None):
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def main_window(app):
    """MainWindowのインスタンスを作成するフィクスチャ"""
    window = MainWindow()
    return window

def test_window_title(main_window):
    """ウィンドウタイトルのテスト"""
    assert main_window.windowTitle() == "マイエディタ"

def test_window_geometry(main_window):
    """ウィンドウのジオメトリのテスト"""
    assert main_window.geometry().x() == 100
    assert main_window.geometry().y() == 100
    assert main_window.geometry().width() == 800
    assert main_window.geometry().height() == 600

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
    assert "&開く" in actions
    assert "&保存" in actions
    assert "&終了" in actions

def test_open_file_action(main_window, mocker):
    """ファイルを開くアクションのテスト"""
    mocker.patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=("test.txt", ""))
    mocker.patch('my_package.editor.FileEditor.open_file')
    main_window.open_file()
    assert main_window.tab_manager.count() == 2

def test_save_file_action(main_window, mocker):
    """ファイルを保存するアクションのテスト"""
    mocker.patch('my_package.editor.FileEditor.save_file')
    main_window.save_file()
    current_widget = main_window.tab_manager.currentWidget()
    if isinstance(current_widget, FileEditor):
        current_widget.save_file.assert_called_once()