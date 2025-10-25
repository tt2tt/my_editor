from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from logging_config import setup_logging


def build_windows_exe(source: Path, output_dir: Path | None = None, *, name: str = "my_editor") -> int:
    """PyInstallerを用いてWindows用の実行ファイルをビルドする。

    Args:
        source (Path): エントリーポイントとなるPythonファイル。
        output_dir (Path | None): ビルド成果物を格納するディレクトリ。省略時は `dist/`。
        name (str): 生成する実行ファイル名。

    Returns:
        int: PyInstallerの終了コード。
    """
    # ログ出力先を準備し、ビルド開始を記録する。
    log_path = Path.cwd() / "logs" / "build.log"
    logger = setup_logging(log_path)
    logger.info("PyInstallerビルドを開始します。")

    # PyInstallerコマンドを組み立てる。
    dist_path = output_dir or Path.cwd() / "dist"
    build_cmd: list[str] = [
        "pyinstaller",
        str(source),
        "--name",
        name,
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--distpath",
        str(dist_path),
    ]

    # コマンドを実行し、終了コードを呼び出し元に返す。
    logger.debug("PyInstallerコマンド: %s", " ".join(build_cmd))
    result = subprocess.run(build_cmd, check=False, text=True)  # noqa: S603
    logger.info("PyInstallerが終了コード%sで終了しました。", result.returncode)
    return result.returncode


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(description="PyInstallerを用いたビルドツール")
    parser.add_argument("source", type=Path, help="エントリーポイントのPythonファイル")
    parser.add_argument("--output", type=Path, default=None, help="成果物の出力先ディレクトリ")
    parser.add_argument("--name", type=str, default="my_editor", help="生成する実行ファイル名")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """コマンドライン引数を処理してビルドを実行する。"""
    args = parse_args(argv)
    return build_windows_exe(args.source, args.output, name=args.name)


if __name__ == "__main__":
    sys.exit(main())
