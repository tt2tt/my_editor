from __future__ import annotations

import logging
from pathlib import Path

from exceptions import FileOperationError


class FileModel:
    """ファイルの読み書きと開いているファイル一覧を管理するモデル。"""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """ロガーを受け取り内部状態を初期化する。

        Args:
            logger (logging.Logger | None): 外部から注入可能なロガー。省略時は共通ロガーを利用する。
        """
        # ロガーと開いているファイル集合を準備する。
        self._logger = logger or logging.getLogger("my_editor.file_model")
        self._open_files: set[Path] = set()

    def load_file(self, path: Path, *, encoding: str = "utf-8") -> str:
        """指定パスのファイルを読み込んで内容を返す。

        Args:
            path (Path): 読み込む対象のファイルパス。
            encoding (str): ファイルのエンコーディング。デフォルトはUTF-8。

        Returns:
            str: 読み込んだテキスト内容。

        Raises:
            FileOperationError: 読み込みに失敗した場合。
        """
        normalized_path = path.expanduser()
        resolved_path = normalized_path.resolve(strict=False)

        # ファイルを読み込み、失敗時はアプリ共通例外へ変換する。
        try:
            content = self._read_text_with_fallback(resolved_path, encoding)
        except OSError as exc:
            self._logger.error("ファイルの読み込みに失敗しました: %s", resolved_path, exc_info=exc)
            raise FileOperationError(f"ファイルの読み込みに失敗しました: {resolved_path}") from exc
        except UnicodeDecodeError as exc:
            self._logger.error("サポートされていないエンコーディングです: %s", resolved_path, exc_info=exc)
            raise FileOperationError(f"ファイルのデコードに失敗しました: {resolved_path}") from exc

        # 正常に読み込めた場合は開いているファイル一覧へ追加する。
        self._register_open_file(resolved_path)
        self._logger.info("ファイルを読み込みました: %s", resolved_path)
        return content

    def save_file(self, path: Path, content: str, *, encoding: str = "utf-8") -> None:
        """指定パスへテキストを保存する。

        Args:
            path (Path): 書き込み先のファイルパス。
            content (str): 保存するテキスト内容。
            encoding (str): ファイルのエンコーディング。デフォルトはUTF-8。

        Raises:
            FileOperationError: 保存処理に失敗した場合。
        """
        normalized_path = path.expanduser()
        resolved_path = normalized_path.resolve(strict=False)

        # ファイルを書き込み、失敗時は例外を共通形式へ変換する。
        try:
            resolved_path.write_text(content, encoding=encoding)
        except OSError as exc:
            self._logger.error("ファイルの保存に失敗しました: %s", resolved_path, exc_info=exc)
            raise FileOperationError(f"ファイルの保存に失敗しました: {resolved_path}") from exc

        # 成功した場合は開いているファイルとして追跡しログを残す。
        self._register_open_file(resolved_path)
        self._logger.info("ファイルを保存しました: %s", resolved_path)

    def list_open_files(self) -> list[Path]:
        """現在開いているファイルパス一覧を返す。"""
        # ソートしたリストで返し、テストしやすい決定的な順序を保証する。
        return sorted(self._open_files)

    def _register_open_file(self, path: Path) -> None:
        """開いているファイル集合へパスを登録する。"""
        self._open_files.add(path)

    def _read_text_with_fallback(self, path: Path, primary_encoding: str) -> str:
        """可能なエンコーディングを順に試してテキストを読み込む。"""
        candidates = [primary_encoding, "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "cp932"]
        tried: set[str] = set()

        for encoding in candidates:
            if encoding in tried:
                continue
            tried.add(encoding)
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError as exc:
                self._logger.debug(
                    "エンコーディングの判定に失敗しました: path=%s encoding=%s",
                    path,
                    encoding,
                    exc_info=exc,
                )
                continue

        raise UnicodeDecodeError(primary_encoding, b"", 0, 0, "デコード可能なエンコーディングが見つかりません")

