from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QMainWindow, QPushButton, QSplitter, QVBoxLayout, QWidget

from views.editor_tab_widget import EditorTabWidget
from views.folder_tree import FolderTree


class MainWindow(QMainWindow):
    """アプリケーションのメインウィンドウ。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        """初期レイアウトを構築する。

        Args:
            parent (QWidget | None): 親ウィジェット。省略可。
        """
        # 親クラスの初期化を実行する。
        super().__init__(parent)

        # ウィンドウタイトルと初期サイズを設定する。
        self.setWindowTitle("My Editor")
        self.resize(1200, 800)
        self.statusBar()

        # UI構築とシグナル接続を実行する。
        self._build_layout()
        self._connect_signals()
        self._bind_actions()

    def _build_layout(self) -> None:
        """メインウィンドウのレイアウトを構築する。"""
        # 中央ウィジェットと基本レイアウトを準備する。
        self._central_container = QWidget(self)
        main_layout = QHBoxLayout(self._central_container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # スプリッターを用いてフォルダビューとエディタ領域を左右に分割する。
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal, self._central_container)
        self._main_splitter.setObjectName("mainSplitter")
        main_layout.addWidget(self._main_splitter)

        # 左側: フォルダツリー領域。
        self._folder_tree = FolderTree(self._main_splitter)
        self._folder_tree.setObjectName("folderTree")
        self._main_splitter.addWidget(self._folder_tree)

        # 右側: エディタ領域とチャットUIをまとめる縦レイアウト。
        editor_panel = QWidget(self._main_splitter)
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(8)

        # エディタタブウィジェットを配置する。
        self._tab_widget = EditorTabWidget(editor_panel)
        self._tab_widget.setObjectName("editorTabs")
        editor_layout.addWidget(self._tab_widget)

        # チャット入力と送信ボタンを横並びで配置する。
        chat_container = QWidget(editor_panel)
        chat_layout = QHBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(4)

        self._chat_input = QLineEdit(chat_container)
        self._chat_input.setObjectName("chatInput")
        chat_layout.addWidget(self._chat_input)

        self._send_button = QPushButton("送信", chat_container)
        self._send_button.setObjectName("sendButton")
        chat_layout.addWidget(self._send_button)

        editor_layout.addWidget(chat_container)
        self._main_splitter.addWidget(editor_panel)
        self._main_splitter.setStretchFactor(0, 1)
        self._main_splitter.setStretchFactor(1, 3)

        self.setCentralWidget(self._central_container)

    def _connect_signals(self) -> None:
        """ウィジェット間のシグナルを接続する。"""
        self._send_button.clicked.connect(self._handle_chat_submit)
        self._chat_input.returnPressed.connect(self._handle_chat_submit)

    def _bind_actions(self) -> None:
        """メニューバーのアクションを初期化する。"""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("ファイル")

        self._action_open_file = QAction("開く...", self)
        self._action_open_file.setShortcut(QKeySequence.StandardKey.Open)
        file_menu.addAction(self._action_open_file)

        self._action_open_folder = QAction("フォルダを開く...", self)
        self._action_open_folder.setShortcut(QKeySequence("Ctrl+Shift+O"))
        file_menu.addAction(self._action_open_folder)

        self._action_save_file = QAction("保存", self)
        self._action_save_file.setShortcut(QKeySequence.StandardKey.Save)
        file_menu.addAction(self._action_save_file)

        self._action_close_tab = QAction("タブを閉じる", self)
        self._action_close_tab.setShortcut(QKeySequence.StandardKey.Close)
        file_menu.addAction(self._action_close_tab)

        self._action_open_settings = QAction("OpenAI設定...", self)
        self._action_open_settings.setShortcut(QKeySequence.StandardKey.Preferences)
        file_menu.addAction(self._action_open_settings)

    def _handle_chat_submit(self) -> None:
        """チャット入力の送信要求を処理する。"""
        text = self._chat_input.text().strip()
        if not text:
            return

        self.statusBar().showMessage(f"チャット送信: {text}", 2000)
        self._chat_input.clear()

    @property
    def folder_view(self) -> FolderTree:
        """フォルダツリーウィジェットを返す。互換目的のエイリアス。"""
        return self._folder_tree

    @property
    def folder_tree(self) -> FolderTree:
        """フォルダツリーウィジェットを返す。"""
        return self._folder_tree

    @property
    def tab_widget(self) -> EditorTabWidget:
        """エディタタブウィジェットを返す。"""
        return self._tab_widget

    @property
    def chat_input(self) -> QLineEdit:
        """チャット入力フィールドを返す。"""
        return self._chat_input

    @property
    def send_button(self) -> QPushButton:
        """チャット送信ボタンを返す。"""
        return self._send_button

    @property
    def action_open_file(self) -> QAction:
        """ファイルを開くアクションを返す。"""
        return self._action_open_file

    @property
    def action_save_file(self) -> QAction:
        """ファイル保存アクションを返す。"""
        return self._action_save_file

    @property
    def action_close_tab(self) -> QAction:
        """タブを閉じるアクションを返す。"""
        return self._action_close_tab

    @property
    def action_open_folder(self) -> QAction:
        """フォルダを開くアクションを返す。"""
        return self._action_open_folder

    @property
    def action_open_settings(self) -> QAction:
        """OpenAI設定を開くアクションを返す。"""
        return self._action_open_settings
