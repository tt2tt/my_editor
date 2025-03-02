import sys
import os
import re
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QWidget, QFileDialog, QToolBar, QLineEdit, QCheckBox, QPushButton
from PySide6.QtGui import QAction, QKeySequence, QTextCursor
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
        self.setFocusPolicy(Qt.StrongFocus)  # ショートカットが発生するようフォーカスを明示的に要求
        # 新規属性：前回の検索パターンと最後のヒット位置
        self.last_search_pattern = ""
        self.last_match_end = 0

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

        # 追加: フォルダを開くアクションを追加
        open_folder_action = QAction("&フォルダを開く", self)
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)

        save_action = QAction("&保存", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        exit_action = QAction("&終了", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 編集メニューを追加
        edit_menu = QMenu("&編集", self)
        menu_bar.addMenu(edit_menu)
        undo_action = QAction("&元に戻す", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.undo_edit)
        edit_menu.addAction(undo_action)
        
        # 追加: やり直す機能のアクション
        redo_action = QAction("やり直す", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.redo_edit)
        edit_menu.addAction(redo_action)

    def open_file(self):
        """ファイルを開く"""
        file_path, _ = QFileDialog.getOpenFileName(self, "ファイルを開く", "", "All Files (*);;Text Files (*.txt)")
        if file_path:
            editor = FileEditor()
            editor.open_file(file_path)
            file_name = os.path.basename(file_path)
            self.tab_manager.add_new_tab(file_name, editor)
            self.tab_manager.setCurrentWidget(editor)

    # フォルダを開く機能
    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "フォルダを開く", "")
        if folder_path:
            from PySide6.QtWidgets import QSplitter, QTreeView, QTabWidget, QFileSystemModel
            splitter = QSplitter()  # 水平分割
            # 左側：フォルダツリー
            tree_view = QTreeView()
            # ツリービューの最大幅を設定して表示を小さくする
            tree_view.setMaximumWidth(200)
            model = QFileSystemModel(tree_view)
            model.setRootPath(folder_path)
            tree_view.setModel(model)
            tree_view.setRootIndex(model.index(folder_path))
            splitter.addWidget(tree_view)
            # ツリー領域を全体の1/5に設定
            splitter.setStretchFactor(0, 1)
            # 右側：内部タブ（ファイルエディタ用）
            internal_tabs = QTabWidget()
            splitter.addWidget(internal_tabs)
            # 内部タブ領域を全体の4/5に設定
            splitter.setStretchFactor(1, 4)
            
            # ツリー上でダブルクリックされたとき、内部タブにファイルを追加
            def on_treeview_doubleClicked(index):
                file_path = model.filePath(index)
                if os.path.isfile(file_path):
                    editor = FileEditor()
                    editor.open_file(file_path)
                    file_name = os.path.basename(file_path)
                    internal_tabs.addTab(editor, file_name)
                    internal_tabs.setCurrentWidget(editor)
            tree_view.doubleClicked.connect(on_treeview_doubleClicked)
            
            folder_name = os.path.basename(folder_path)
            self.tab_manager.add_new_tab(folder_name, splitter)
            self.tab_manager.setCurrentWidget(splitter)

    def new_file(self):
        """新しいファイルを作成する"""
        print(2/0)
        editor = FileEditor()
        self.tab_manager.add_new_tab("新しいファイル", editor)
        self.tab_manager.setCurrentWidget(editor)

    def save_file(self):
        """ファイルを保存する"""
        current_widget = self.tab_manager.currentWidget()
        file_editor = None
        if isinstance(current_widget, FileEditor):
            file_editor = current_widget
        else:
            from PySide6.QtWidgets import QTabWidget
            internal_tabs = current_widget.findChild(QTabWidget)
            if internal_tabs:
                candidate = internal_tabs.currentWidget()
                if isinstance(candidate, FileEditor):
                    file_editor = candidate
        if file_editor is not None:
            if file_editor.current_file is None:
                file_path, _ = QFileDialog.getSaveFileName(self, "ファイルを保存", "", "All Files (*);;Text Files (*.txt)")
                if file_path:
                    file_editor.save_file(file_path)
                    file_name = os.path.basename(file_path)
                    if isinstance(current_widget, FileEditor):
                        index = self.tab_manager.indexOf(current_widget)
                        self.tab_manager.setTabText(index, file_name)
                    else:
                        internal_tabs.setTabText(internal_tabs.indexOf(file_editor), file_name)
            else:
                file_editor.save_file()

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

        # 検索欄
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("検索...")
        self.search_box.returnPressed.connect(self.search_text)
        self.tool_bar.addWidget(self.search_box)
        
        # 置換欄と置換ボタンを追加
        self.replace_box = QLineEdit(self)
        self.replace_box.setPlaceholderText("置換...")
        self.tool_bar.addWidget(self.replace_box)
        
        self.replace_button = QPushButton("置換", self)
        self.replace_button.clicked.connect(self.replace_text)
        self.tool_bar.addWidget(self.replace_button)
        
        # 全置換ボタンを追加
        self.replace_all_button = QPushButton("全置換", self)
        self.replace_all_button.clicked.connect(self.replace_all_text)
        self.tool_bar.addWidget(self.replace_all_button)
        
        # 正規表現利用の有無を切り替えるチェックボックス
        self.regex_checkbox = QCheckBox("正規表現", self)
        self.regex_checkbox.setChecked(False)
        self.tool_bar.addWidget(self.regex_checkbox)
        
        self.tool_bar.setMovable(False)
        self.tool_bar.setFloatable(False)
        self.tool_bar.hide()

    def search_text(self):
        """検索テキストを、正規表現モードかリテラルモードかでハイライトする"""
        # FileEditor を直接または内部タブから取得するように変更
        current_widget = self.tab_manager.currentWidget()
        file_editor = None
        if isinstance(current_widget, FileEditor):
            file_editor = current_widget
        else:
            from PySide6.QtWidgets import QTabWidget
            internal_tabs = current_widget.findChild(QTabWidget)
            if internal_tabs:
                candidate = internal_tabs.currentWidget()
                if isinstance(candidate, FileEditor):
                    file_editor = candidate
        if file_editor is not None:
            pattern = self.search_box.text()
            if pattern:
                text = file_editor.toPlainText()
                if self.regex_checkbox.isChecked():
                    try:
                        regex = re.compile(pattern, re.DOTALL)
                    except re.error:
                        return
                    start_pos = self.last_match_end if pattern == self.last_search_pattern else 0
                    match = regex.search(text, start_pos)
                    if not match:
                        match = regex.search(text, 0)
                    if match:
                        cursor = file_editor.textCursor()
                        cursor.setPosition(match.start())
                        cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
                        file_editor.setTextCursor(cursor)
                        self.last_match_end = match.end()
                        self.last_search_pattern = pattern
                    else:
                        self.last_search_pattern = ""
                        self.last_match_end = 0
                else:
                    start_pos = self.last_match_end if pattern == self.last_search_pattern else 0
                    match_cursor = file_editor.document().find(pattern, start_pos)
                    if match_cursor.isNull():
                        match_cursor = file_editor.document().find(pattern, 0)
                    if not match_cursor.isNull():
                        file_editor.setTextCursor(match_cursor)
                        self.last_match_end = match_cursor.selectionEnd()
                        self.last_search_pattern = pattern
                    else:
                        self.last_search_pattern = ""
                        self.last_match_end = 0
        self.search_box.setFocus()

    def replace_text(self):
        """現在の選択部分を置換欄の内容で置換し、次のヒットを検索する"""
        current_widget = self.tab_manager.currentWidget()
        file_editor = None
        if isinstance(current_widget, FileEditor):
            file_editor = current_widget
        else:
            from PySide6.QtWidgets import QTabWidget
            internal_tabs = current_widget.findChild(QTabWidget)
            if internal_tabs:
                candidate = internal_tabs.currentWidget()
                if isinstance(candidate, FileEditor):
                    file_editor = candidate
        if file_editor is not None:
            replacement = self.replace_box.text()
            cursor = file_editor.textCursor()
            if cursor.selectedText() != "":
                cursor.insertText(replacement)
                self.search_text()

    def replace_all_text(self):
        """全置換機能：全ての検索対象を置換欄の内容で置換する"""
        current_widget = self.tab_manager.currentWidget()
        file_editor = None
        if isinstance(current_widget, FileEditor):
            file_editor = current_widget
        else:
            from PySide6.QtWidgets import QTabWidget
            internal_tabs = current_widget.findChild(QTabWidget)
            if internal_tabs:
                candidate = internal_tabs.currentWidget()
                if isinstance(candidate, FileEditor):
                    file_editor = candidate
        if file_editor is not None:
            search_pattern = self.search_box.text()
            replacement = self.replace_box.text()
            if search_pattern:
                original_text = file_editor.toPlainText()
                new_text = ""
                if self.regex_checkbox.isChecked():
                    try:
                        import re
                        regex = re.compile(search_pattern, re.DOTALL)
                        new_text = regex.sub(replacement, original_text)
                    except re.error:
                        return
                else:
                    new_text = original_text.replace(search_pattern, replacement)
                file_editor.setPlainText(new_text)
            self.last_search_pattern = ""
            self.last_match_end = 0

    def create_shortcuts(self):
        """ショートカットを作成する"""
        search_shortcut = QAction(self)
        search_shortcut.setShortcut(QKeySequence("Ctrl+F"))
        search_shortcut.triggered.connect(self.toggle_search_bar)
        self.addAction(search_shortcut)
		
        # Ctrl+Sでファイルを保存するショートカット
        save_shortcut = QAction(self)
        save_shortcut.setShortcut(QKeySequence("Ctrl+S"))
        save_shortcut.triggered.connect(self.save_file)
        self.addAction(save_shortcut)

    def toggle_search_bar(self):
        """検索バーの表示/非表示を切り替える"""
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

    def undo_edit(self):
        """戻る"""
        current_widget = self.tab_manager.currentWidget()
        # 現在のタブがFileEditorの場合にundoを実行
        if current_widget is not None and hasattr(current_widget, "undo"):
            current_widget.undo()
    
    def redo_edit(self):
        """進む"""
        current_widget = self.tab_manager.currentWidget()
        if current_widget is not None and hasattr(current_widget, "redo"):
            current_widget.redo()

if __name__ == "__main__":
    from my_package.sub_package.my_logger import MyLogger
    logger = MyLogger().get_logger()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    logger.info("イベントループ開始")
    try:
        exit_code = app.exec()
    except Exception as e:
        logger.error("イベントループの途中で例外が発生しました: %s", e)
    finally:
        logger.info("イベントループ終了")
    sys.exit(exit_code)