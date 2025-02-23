import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu
from PySide6.QtGui import QAction

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("マイエディタ")
        self.setGeometry(100, 100, 800, 600)
        self.apply_styles()
        self.create_menu_bar()

    def apply_styles(self):
        style_path = os.path.join(os.path.dirname(__file__), 'QSS', 'style.qss')
        with open(style_path, 'r') as style_file:
            self.setStyleSheet(style_file.read())

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = QMenu("&ファイル", self)
        menu_bar.addMenu(file_menu)

        open_action = QAction("&開く", self)
        file_menu.addAction(open_action)

        save_action = QAction("&保存", self)
        file_menu.addAction(save_action)

        exit_action = QAction("&終了", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())