from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import build_exe


def test_build_windows_exe_invokes_pyinstaller_default_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """build_windows_exeがデフォルト設定でPyInstallerを呼び出すことを検証する。"""
    recorded: dict[str, object] = {}

    class DummyLogger:
        """ログメッセージを無視するテスト用ロガー。"""

        def info(self, *args: object, **kwargs: object) -> None:
            """INFOログを無視する。"""

        def debug(self, *args: object, **kwargs: object) -> None:
            """DEBUGログを無視する。"""

    # ロガーとPyInstaller呼び出しをモック化し、副作用なく検証できるようにする。
    def fake_setup_logging(path: Path) -> DummyLogger:
        recorded["log_path"] = path
        return DummyLogger()

    def fake_run(*args: object, **kwargs: object) -> SimpleNamespace:
        recorded["run_args"] = args
        recorded["run_kwargs"] = kwargs
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(build_exe, "setup_logging", fake_setup_logging)
    monkeypatch.setattr(build_exe.subprocess, "run", fake_run)

    # ビルド対象とカレントディレクトリを事前に用意する。
    monkeypatch.chdir(tmp_path)
    source = Path("main.py")

    # ビルド処理を実行し、終了コードやコマンド内容を検証する。
    exit_code = build_exe.build_windows_exe(source)
    expected_command = (
        [
            "pyinstaller",
            str(source),
            "--name",
            "my_editor",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--distpath",
            str(tmp_path / "dist"),
        ],
    )

    assert exit_code == 0
    assert recorded["log_path"] == tmp_path / "logs" / "build.log"
    assert recorded["run_args"] == expected_command
    assert recorded["run_kwargs"] == {"check": False, "text": True}


def test_main_parses_arguments(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """mainがCLI引数を解析してbuild_windows_exeを呼び出すことを検証する。"""
    called: dict[str, Path | None | str] = {}

    # build_windows_exeをモック化し、引数が期待通りかを確認する。
    def fake_build(source: Path, output_dir: Path | None, *, name: str) -> int:
        called["source"] = source
        called["output_dir"] = output_dir
        called["name"] = name
        return 42

    monkeypatch.setattr(build_exe, "build_windows_exe", fake_build)

    # CLI引数を模擬してmain関数を実行する。
    argv = [
        str(tmp_path / "entry.py"),
        "--output",
        str(tmp_path / "custom"),
        "--name",
        "custom_app",
    ]
    result = build_exe.main(argv)

    assert result == 42
    assert called["source"] == tmp_path / "entry.py"
    assert called["output_dir"] == tmp_path / "custom"
    assert called["name"] == "custom_app"
