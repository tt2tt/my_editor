from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget


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

        # メインコンテナを初期化しプレースホルダーを配置する。
        container = QWidget(self)
        layout = QVBoxLayout(container)

        # 仮のラベルを用意して将来のUIスペースを確保する。
        placeholder_label = QLabel("エディタ初期化中...", container)
        layout.addWidget(placeholder_label)

        # レイアウト済みコンテナを中央にセットする。
        self.setCentralWidget(container)
