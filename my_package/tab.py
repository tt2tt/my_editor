from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QLabel

class TabManager(QTabWidget):
    def __init__(self, parent=None):
        """TabManagerの初期化"""
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.remove_tab)

    def add_new_tab(self, title="新しいタブ"):
        """新しいタブを追加する"""
        new_tab = QWidget()
        layout = QVBoxLayout()
        label = QLabel("コンテンツ")
        layout.addWidget(label)
        new_tab.setLayout(layout)
        self.addTab(new_tab, title)

    def remove_tab(self, index):
        """指定されたインデックスのタブを削除する"""
        self.removeTab(index)
