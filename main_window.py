import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QWidget, QFileDialog, QToolBar, QLineEdit
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt
from my_package.tab import TabManager
from my_package.editor import FileEditor

class MainWindow(QMainWindow):
    def __init__(self):
        """MainWindowの初期化"""
        super().__init__()
        self.setWindowTitle("マイエディタ")
        self.setGeometry(100, 100, 800, 600)
        self.apply_styles()
        self.create_menu_bar()
        self.create_tab_manager()
        self.create_tool_bar()
        self.create_shortcuts()

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

        new_action = QAction("&新しいファイル", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("&ファイルを開く", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("&保存", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        exit_action = QAction("&終了", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def open_file(self):
        """ファイルを開く"""
        file_path, _ = QFileDialog.getOpenFileName(self, "ファイルを開く", "", "All Files (*);;Text Files (*.txt)")
        if file_path:
            editor = FileEditor()
            editor.open_file(file_path)
            file_name = os.path.basename(file_path)
            self.tab_manager.add_new_tab(file_name, editor)
            self.tab_manager.setCurrentWidget(editor)

    def new_file(self):
        """新しいファイルを作成する"""
        editor = FileEditor()
        self.tab_manager.add_new_tab("新しいファイル", editor)
        self.tab_manager.setCurrentWidget(editor)

    def save_file(self):
        """ファイルを保存する"""
        current_widget = self.tab_manager.currentWidget()
        if isinstance(current_widget, FileEditor):
            if current_widget.current_file is None:
                file_path, _ = QFileDialog.getSaveFileName(self, "ファイルを保存", "", "All Files (*);;Text Files (*.txt)")
                if file_path:
                    current_widget.save_file(file_path)
            else:
                current_widget.save_file()

    def create_tab_manager(self):
        """TabManagerを作成して表示する"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tab_manager = TabManager(self)
        layout.addWidget(self.tab_manager)

    def create_tool_bar(self):
        """ツールバーを作成する"""
        self.tool_bar = QToolBar("Search Toolbar", self)
        self.addToolBar(Qt.TopToolBarArea, self.tool_bar)

        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("検索...")
        self.search_box.returnPressed.connect(self.search_text)
        self.tool_bar.addWidget(self.search_box)
        self.tool_bar.setMovable(False)
        self.tool_bar.setFloatable(False)
        self.tool_bar.hide()

    def search_text(self):
        """検索テキストをハイライトする"""
        current_widget = self.tab_manager.currentWidget()
        if isinstance(current_widget, FileEditor):
            search_text = self.search_box.text()
            if search_text:
                cursor = current_widget.textCursor()
                document = current_widget.document()
                found_cursor = document.find(search_text, cursor)
                if found_cursor.isNull():
                    found_cursor = document.find(search_text)
                if not found_cursor.isNull():
                    current_widget.setTextCursor(found_cursor)
            current_widget.setFocus()

    def create_shortcuts(self):
        """ショートカットを作成する"""
        search_shortcut = QAction(self)
        search_shortcut.setShortcut(QKeySequence("Ctrl+F"))
        search_shortcut.triggered.connect(self.toggle_search_bar)
        self.addAction(search_shortcut)

    def toggle_search_bar(self):
        """検索バーの表示/非表示を切り替える"""
        current_widget = self.tab_manager.currentWidget()
        if isinstance(current_widget, FileEditor):
            if self.tool_bar.isVisible():
                self.tool_bar.hide()
            else:
                self.tool_bar.show()
                self.search_box.setFocus()

    def wheelEvent(self, event):
        """ホイールイベントを処理して拡大・縮小を行う"""
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()

    def zoom_in(self):
        """拡大する"""
        current_widget = self.tab_manager.currentWidget()
        if isinstance(current_widget, FileEditor):
            current_widget.zoom_in()

    def zoom_out(self):
        """縮小する"""
        current_widget = self.tab_manager.currentWidget()
        if isinstance(current_widget, FileEditor):
            current_widget.zoom_out()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())