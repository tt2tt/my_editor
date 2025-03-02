import logging
from logging.handlers import TimedRotatingFileHandler

class MyLogger:
    def __init__(self, log_file="./log/app.log", when="D", interval=1, backup_count=7):
        """
        日付ベースのログローテーションを行うロガー
        :param log_file: ログファイル名
        :param when: ローテーションの間隔
        :param interval: ローテーションの間隔数
        :param backup_count: 保持するバックアップファイルの最大数
        """
        self.logger = logging.getLogger("TimedRotatingLogger")
        self.logger.setLevel(logging.DEBUG)

        # コンソールハンドラーを作成
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # ファイルハンドラーを作成
        file_handler = TimedRotatingFileHandler(
            log_file, when=when, interval=interval, backupCount=backup_count, encoding="utf-8"
        )

        # フォーマッターを設定
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # ロガーにハンドラーを追加
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)


    def get_logger(self):
        """
        ロガーインスタンスを取得
        :return: ロガーオブジェクト
        """
        return self.logger