from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    """pytestの初期化時にプロジェクトルートをパスへ追加する。"""
    # プロジェクトルートを特定する。
    project_root = Path(__file__).resolve().parent.parent

    # 既にパスへ追加されていない場合のみ追加する。
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
