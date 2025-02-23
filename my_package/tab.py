from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QLabel

class TabManager(QTabWidget):
    def __init__(self, parent=None):
        """TabManagerの初期化"""
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.remove_tab)

    def add_new_tab(self, title="新しいタブ", widget=None):
        """新しいタブを追加する"""
        if widget is None:
            widget = QWidget()
            layout = QVBoxLayout()
            label = QLabel("コンテンツ")
            layout.addWidget(label)
            widget.setLayout(layout)
        self.addTab(widget, title)

    def remove_tab(self, index):
        """指定されたインデックスのタブを削除する"""
        self.removeTab(index)
