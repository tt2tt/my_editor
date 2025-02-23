import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QWidget
from PySide6.QtGui import QAction
from my_package.tab import TabManager

class MainWindow(QMainWindow):
    def __init__(self):
        """MainWindowの初期化"""
        super().__init__()
        self.setWindowTitle("マイエディタ")
        self.setGeometry(100, 100, 800, 600)
        self.apply_styles()
        self.create_menu_bar()
        self.create_tab_manager()

    def apply_styles(self):
        """スタイルシートを適用する"""
        style_path = os.path.join(os.path.dirname(__file__), 'QSS', 'style.qss')
        with open(style_path, 'r') as style_file:
            self.setStyleSheet(style_file.read())

    def create_menu_bar(self):
        """メニューバーを作成する"""
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

    def create_tab_manager(self):
        """TabManagerを作成して表示する"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tab_manager = TabManager(self)
        layout.addWidget(self.tab_manager)

        # デフォルトのタブを追加
        self.tab_manager.add_new_tab("デフォルトタブ")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())