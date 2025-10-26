from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


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

        # 左側: フォルダツリー領域 (現時点ではリストで仮実装)。
        self._folder_list = QListWidget(self._main_splitter)
        self._folder_list.setObjectName("folderList")
        self._folder_list.addItem("プロジェクトルート")
        self._main_splitter.addWidget(self._folder_list)

        # 右側: エディタ領域とチャットUIをまとめる縦レイアウト。
        editor_panel = QWidget(self._main_splitter)
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(8)

        # エディタタブのプレースホルダーを用意する。
        self._tab_widget = QTabWidget(editor_panel)
        self._tab_widget.setObjectName("editorTabs")
        welcome_label = QLabel("ここにエディタコンテンツが表示されます。", self._tab_widget)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tab_widget.addTab(welcome_label, "スタート")
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

    def _handle_chat_submit(self) -> None:
        """チャット入力の送信要求を処理する。"""
        text = self._chat_input.text().strip()
        if not text:
            return

        self.statusBar().showMessage(f"チャット送信: {text}", 2000)
        self._chat_input.clear()

    @property
    def folder_view(self) -> QListWidget:
        """フォルダリストウィジェットを返す。"""
        return self._folder_list

    @property
    def tab_widget(self) -> QTabWidget:
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
