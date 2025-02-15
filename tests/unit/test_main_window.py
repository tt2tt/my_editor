import pytest
from PySide6.QtWidgets import QApplication
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
    return window

def test_window_title(main_window):
    assert main_window.windowTitle() == "マイエディタ"

def test_window_geometry(main_window):
    assert main_window.geometry().x() == 100
    assert main_window.geometry().y() == 100
    assert main_window.geometry().width() == 800
    assert main_window.geometry().height() == 600