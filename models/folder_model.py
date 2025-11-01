from __future__ import annotations

import logging
from pathlib import Path

from exceptions import FileOperationError


class FolderModel:
    """フォルダ操作を抽象化するモデル。"""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """ロガーを注入し、インスタンスを初期化する。

        Args:
            logger (logging.Logger | None): 操作用ロガー。省略時は共通ロガー。
        """
        # ロガーを保持し、操作ログを残せるようにする。
        self._logger = logger or logging.getLogger("my_editor.folder_model")

    def list_directory(self, path: Path) -> list[Path]:
        """指定ディレクトリ直下のエントリ一覧を返す。

        Args:
            path (Path): 列挙対象のフォルダパス。

        Returns:
            list[Path]: 発見したエントリのパス一覧。

        Raises:
            FileOperationError: フォルダが存在しない、または列挙に失敗した場合。
        """
        normalized_path = path.expanduser()
        resolved_path = normalized_path.resolve(strict=False)

        # ディレクトリ存在を検証する。
        if not resolved_path.exists():
            self._logger.error("ディレクトリが存在しません: %s", resolved_path)
            raise FileOperationError(f"ディレクトリが存在しません: {resolved_path}")
        if not resolved_path.is_dir():
            self._logger.error("ディレクトリではありません: %s", resolved_path)
            raise FileOperationError(f"ディレクトリではありません: {resolved_path}")

        # ディレクトリを列挙し、失敗時は統一例外を送出する。
        try:
            entries = sorted(resolved_path.iterdir())
        except OSError as exc:
            self._logger.error("ディレクトリの列挙に失敗しました: %s", resolved_path, exc_info=exc)
            raise FileOperationError(f"ディレクトリの列挙に失敗しました: {resolved_path}") from exc

        self._logger.info("ディレクトリを列挙しました: %s", resolved_path)
        return entries

    def create_item(self, path: Path, *, is_dir: bool) -> None:
        """ファイルまたはフォルダを作成する。

        Args:
            path (Path): 生成するファイルまたはフォルダのパス。
            is_dir (bool): True の場合はフォルダ、それ以外はファイルを生成する。

        Raises:
            FileOperationError: 生成に失敗、または既にパスが存在する場合。
        """
        normalized_path = path.expanduser()
        resolved_path = normalized_path.resolve(strict=False)

        if resolved_path.exists():
            self._logger.error("パスが既に存在します: %s", resolved_path)
            raise FileOperationError(f"パスが既に存在します: {resolved_path}")

        parent = resolved_path.parent
        if not parent.exists():
            self._logger.error("親ディレクトリが存在しません: %s", parent)
            raise FileOperationError(f"親ディレクトリが存在しません: {parent}")

        try:
            if is_dir:
                resolved_path.mkdir()
            else:
                resolved_path.touch(exist_ok=False)
        except OSError as exc:
            self._logger.error("項目の生成に失敗しました: %s", resolved_path, exc_info=exc)
            raise FileOperationError(f"項目の生成に失敗しました: {resolved_path}") from exc

        self._logger.info("項目を生成しました: %s", resolved_path)

    def delete_item(self, path: Path) -> None:
        """ファイルまたはフォルダを削除する。

        Args:
            path (Path): 削除対象のパス。

        Raises:
            FileOperationError: 削除対象が存在しない、もしくは削除に失敗した場合。
        """
        normalized_path = path.expanduser()
        resolved_path = normalized_path.resolve(strict=False)

        if not resolved_path.exists():
            self._logger.error("削除対象が存在しません: %s", resolved_path)
            raise FileOperationError(f"削除対象が存在しません: {resolved_path}")

        if resolved_path.is_dir():
            if any(resolved_path.iterdir()):
                self._logger.error("ディレクトリが空ではありません: %s", resolved_path)
                raise FileOperationError(f"ディレクトリが空ではありません: {resolved_path}")

            remover = resolved_path.rmdir
        else:
            remover = resolved_path.unlink

        try:
            remover()
        except OSError as exc:
            self._logger.error("項目の削除に失敗しました: %s", resolved_path, exc_info=exc)
            raise FileOperationError(f"項目の削除に失敗しました: {resolved_path}") from exc

        self._logger.info("項目を削除しました: %s", resolved_path)

    def rename_item(self, old_path: Path, new_path: Path) -> None:
        """ファイルまたはフォルダの名称を変更する。

        Args:
            old_path (Path): 現在のパス。
            new_path (Path): 変更後のパス。

        Raises:
            FileOperationError: リネーム対象が存在しない、または重複・失敗した場合。
        """
        src = old_path.expanduser().resolve(strict=False)
        dst = new_path.expanduser().resolve(strict=False)

        if not src.exists():
            self._logger.error("名称変更対象が存在しません: %s", src)
            raise FileOperationError(f"名称変更対象が存在しません: {src}")

        if dst.exists():
            self._logger.error("名称変更後のパスが既に存在します: %s", dst)
            raise FileOperationError(f"名称変更後のパスが既に存在します: {dst}")

        if src.parent != dst.parent:
            self._logger.error("親ディレクトリを跨ぐ名称変更はサポートされていません: %s -> %s", src, dst)
            raise FileOperationError("異なる親ディレクトリへの名称変更はサポートされていません。")

        try:
            src.rename(dst)
        except OSError as exc:
            self._logger.error("名称変更に失敗しました: %s -> %s", src, dst, exc_info=exc)
            raise FileOperationError(f"名称変更に失敗しました: {src} -> {dst}") from exc

        self._logger.info("項目の名称を変更しました: %s -> %s", src, dst)
