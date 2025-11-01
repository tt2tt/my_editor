from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QSplitter, QVBoxLayout, QWidget

from views.editor_tab_widget import EditorTabWidget
from views.folder_tree import FolderTree
from views.chat_panel import ChatPanel


class MainWindow(QMainWindow):
    """アプリケーションのメインウィンドウ。"""

    chat_submitted = Signal(str)
    chat_edit_requested = Signal(str)
    chat_attachment_requested = Signal()

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

        # 右側: エディタタブとチャットパネルを並列配置する。
        self._editor_splitter = QSplitter(Qt.Orientation.Horizontal, self._main_splitter)
        self._editor_splitter.setObjectName("editorSplitter")
        self._main_splitter.addWidget(self._editor_splitter)

        self._tab_widget = EditorTabWidget(self._editor_splitter)
        self._tab_widget.setObjectName("editorTabs")
        self._editor_splitter.addWidget(self._tab_widget)

        self._chat_panel = ChatPanel(self._editor_splitter)
        self._chat_panel.setObjectName("chatPanel")
        self._editor_splitter.addWidget(self._chat_panel)

        self._main_splitter.setStretchFactor(0, 1)
        self._main_splitter.setStretchFactor(1, 3)
        self._editor_splitter.setStretchFactor(0, 3)
        self._editor_splitter.setStretchFactor(1, 2)

        self.setCentralWidget(self._central_container)

    def _connect_signals(self) -> None:
        """ウィジェット間のシグナルを接続する。"""
        self._chat_panel.completion_requested.connect(self._handle_chat_submit)
        self._chat_panel.edit_requested.connect(self._handle_chat_edit_request)
        self._chat_panel.attachment_requested.connect(self._handle_chat_attachment_request)

    def _bind_actions(self) -> None:
        """メニューバーのアクションを初期化する。"""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("ファイル")

        self._action_new_file = QAction("新規ファイル", self)
        self._action_new_file.setShortcut(QKeySequence.StandardKey.New)
        file_menu.addAction(self._action_new_file)

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

    def _handle_chat_submit(self, message: str) -> None:
        """チャット入力の送信要求を処理する。"""
        text = message.strip()
        if not text:
            self.statusBar().showMessage("チャットエラー: メッセージを入力してください。", 3000)
            return

        summary = self._chat_panel.attachment_summary()
        display_text = f"{text}\n{summary}" if summary else text

        self._chat_panel.append_user_message(display_text)
        status = f"チャット送信: {text}"
        if summary:
            status = f"{status} ({summary})"
        self.statusBar().showMessage(status, 2000)
        self.chat_submitted.emit(text)

    def show_chat_response(self, response: str) -> None:
        """AIからの応答メッセージを表示する。"""
        self._chat_panel.append_ai_message(response)
        self.statusBar().showMessage(f"AI応答: {response}", 5000)

    def show_chat_error(self, message: str) -> None:
        """チャット処理で発生したエラーを表示する。"""
        self._chat_panel.append_ai_message(f"エラー: {message}")
        self.statusBar().showMessage(f"チャットエラー: {message}", 5000)

    def _handle_chat_attachment_request(self) -> None:
        """チャット添付リクエストを処理する。"""
        self.statusBar().showMessage("チャット: ファイル選択を開始します。", 2000)
        self.chat_attachment_requested.emit()

    def _handle_chat_edit_request(self, message: str) -> None:
        """チャット編集リクエストを処理する。"""
        text = message.strip()
        if not text:
            self.statusBar().showMessage("チャットエラー: メッセージを入力してください。", 3000)
            return

        summary = self._chat_panel.attachment_summary()
        if not summary:
            self._chat_panel.set_input_text(text)
            self.statusBar().showMessage("チャットエラー: 添付ファイルを選択してください。", 5000)
            return

        display_text = f"{text}\n{summary}"
        self._chat_panel.append_user_message(display_text)

        status = f"チャット編集送信: {text} ({summary})"
        self.statusBar().showMessage(status, 2000)
        self.chat_edit_requested.emit(text)

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
    def chat_panel(self) -> ChatPanel:
        """チャットパネルを返す。"""
        return self._chat_panel

    @property
    def action_open_file(self) -> QAction:
        """ファイルを開くアクションを返す。"""
        return self._action_open_file

    @property
    def action_new_file(self) -> QAction:
        """新規ファイルを作成するアクションを返す。"""
        return self._action_new_file

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
