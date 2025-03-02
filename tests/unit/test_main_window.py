import os
import pytest
from PySide6.QtWidgets import QApplication, QMenu
from main_window import MainWindow

@pytest.fixture(scope="session")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def main_window(app):
    window = MainWindow()
    window.show()
    return window

def test_window_title(main_window):
    """ウィンドウタイトルのテスト"""
    assert main_window.windowTitle() == "マイエディタ"

def test_window_geometry(main_window):
    """ウィンドウジオメトリのテスト"""
    geom = main_window.geometry()
    assert geom.x() == 100
    assert geom.y() == 100
    assert geom.width() == 800
    assert geom.height() == 600

def test_menu_bar_exists(main_window):
    """メニューバーの存在を検証するテスト"""
    menu_bar = main_window.menuBar()
    assert menu_bar is not None

def test_file_menu_exists(main_window):
    """ファイルメニューが存在するかテスト"""
    menu_bar = main_window.menuBar()
    file_menu = None
    for action in menu_bar.actions():
        if action.menu() and action.text() == "&ファイル":
            file_menu = action.menu()
            break
    assert isinstance(file_menu, QMenu)

def test_file_menu_actions(main_window):
    """ファイルメニューのアクションをテスト"""
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