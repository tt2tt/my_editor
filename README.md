# my_editor

## プロジェクト概要
PySide6 を使用したデスクトップ向けコードエディタです。MVC アーキテクチャを採用し、AI 補助編集、ファイル管理、ログ収集、CI/CD を統合しています。Windows 11 での利用を前提に、PyInstaller による exe パッケージングを想定しています。

## 主な機能
- AI チャットによるコード提案と単一ファイル編集
- タブ型エディタとフォルダブラウズ機能
- グローバル例外ハンドラおよび操作ログ出力
- pytest / mypy / GitHub Actions による CI/CD
- 進捗管理スクリプトによるドキュメント更新自動化

## 必要環境
- Windows 11
- Python 3.11 以上
- PowerShell (同梱のスクリプトは PowerShell 想定)

## セットアップ手順
```powershell
python -m venv .\venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 実行方法
```powershell
.\venv\Scripts\python.exe main.py
```
GUI 起動後はチャットパネルから AI 編集を指示できます。API キーは設定ダイアログから登録してください。

## テストと型チェック
CI と同じコマンドは以下の通りです。
```powershell
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m mypy .
```

## ログと設定
- ログ出力: `logs/application.log` を基点に日次ローテーション (30 日) を実施
- 設定: `SettingsModel` で API キーなどを安全に保存

## 進捗更新
ドキュメント進捗を更新する場合は次を利用します。
```powershell
.\venv\Scripts\python.exe .\scripts\update_progress.py --task 33
```
`document/progress.txt` と `document/roadmap.txt` を同期的に更新できます。

## フォルダ構成 (抜粋)
```
my_editor/
 ├─ app_logging/          # GUIログや行動トラッキング用ハンドラ
 ├─ controllers/          # アプリ全体・AI・ファイル操作などの制御層
 ├─ design/               # PlantUML 図面 (アーキテクチャ・UAT フロー)
 ├─ document/             # 進捗管理やロードマップドキュメント
 ├─ models/               # ファイル・フォルダ・タブ・設定のデータ層
 ├─ scripts/              # ビルドや進捗更新などの補助スクリプト
 ├─ tests/                # pytest ベースの自動テストと手動UAT資料
 ├─ views/                # PySide6 ベースのUIコンポーネント
 └─ main.py               # エントリポイント
```
各ディレクトリがMVC構造と運用作業を支える役割を分担しているため、開発前に上記の構造を把握しておくと修正対象が特定しやすくなります。

## ライセンス
このリポジトリは個人利用目的であり、外部への配布・再利用は許可していません。
