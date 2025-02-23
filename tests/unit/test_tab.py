import pytest
from PySide6.QtWidgets import QApplication
from my_package.tab import TabManager

@pytest.fixture(scope="session")
def app():
    """QApplicationのインスタンスを作成するフィクスチャ"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def tab_manager(app):
    """TabManagerのインスタンスを作成するフィクスチャ"""
    tab_manager = TabManager()
    return tab_manager

def test_add_new_tab(tab_manager):
    """新しいタブを追加するテスト"""
    initial_count = tab_manager.count()
    tab_manager.add_new_tab("テストタブ")
    assert tab_manager.count() == initial_count + 1
    assert tab_manager.tabText(initial_count) == "テストタブ"

def test_remove_tab(tab_manager):
    """タブを削除するテスト"""
    tab_manager.add_new_tab("削除タブ")
    initial_count = tab_manager.count()
    tab_manager.remove_tab(initial_count - 1)
    assert tab_manager.count() == initial_count - 1
