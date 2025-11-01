"""アプリケーション向けのロギング補助機能パッケージ。"""

from .handlers import attach_gui_handler, log_user_action

__all__ = [
    "attach_gui_handler",
    "log_user_action",
]
