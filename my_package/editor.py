from PySide6.QtWidgets import QTextEdit

class FileEditor(QTextEdit):
    def __init__(self, parent=None):
        """FileEditorの初期化"""
        super().__init__(parent)
        self.current_file = None

    def open_file(self, file_path):
        """ファイルを開く"""
        with open(file_path, 'r', encoding='utf-8') as file:
            self.setText(file.read())
        self.current_file = file_path

    def save_file(self, file_path=None):
        """ファイルを保存する"""
        if file_path is None:
            file_path = self.current_file
        if file_path is not None:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.toPlainText())
            self.current_file = file_path
