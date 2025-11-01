# my_editor 利用ガイド

## 1. 事前準備
1. Python 3.11 以上をインストールします。
2. PowerShell を管理者権限なしで実行し、以下のコマンドで仮想環境を準備します。
   ```powershell
   python -m venv .\venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

## 2. アプリケーション起動
1. 仮想環境が有効な状態で次を実行します。
   ```powershell
   .\venv\Scripts\python.exe main.py
   ```
2. 初回起動時は設定メニューから OpenAI API キーを登録してください。
3. メイン画面のフォルダビューで編集対象のディレクトリを選択します。

## 3. ファイル編集ワークフロー
1. フォルダツリーでファイルをダブルクリックすると新しいタブが開きます。
2. 変更するとタブに未保存マークが付きます。`Ctrl+S` で保存可能です。
3. チャットパネルから指示を送ると、AI が提案コードを返し、適用ボタンでエディタに反映できます。

## 4. ログと例外の確認
- すべての操作は `logs/user_actions.log` に JSON 形式で記録されます。
- 予期せぬ例外が発生するとダイアログ表示とともに `logs/application.log` へ重大ログが出力されます。

## 5. テストと型チェック
CI と同等の確認をローカルで実施する場合は以下を順に実行します。
```powershell
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m mypy .
```

## 6. 進捗ドキュメントの更新
1. タスク完了後に進捗を記録するにはスクリプトを用います。
   ```powershell
   .\venv\Scripts\python.exe .\scripts\update_progress.py --task 33 --date 2025-11-02
   ```
2. 複数タスクをまとめて更新する場合は `--task` を複数指定してください。
3. スクリプト実行後は `document/progress.txt` と `document/roadmap.txt` を確認し、意図通りに更新されているかをチェックします。

## 7. exe パッケージ化
1. GitHub Actions では PyInstaller を使用して exe を生成します。
2. ローカルで確認する場合は次を実行します。
   ```powershell
   .\venv\Scripts\python.exe .\scripts\build_exe.py
   ```
3. 成果物は `dist/` 以下に配置されます。

## 8. トラブルシューティング
- `ImportError: No module named 'PySide6'` → 仮想環境内で依存関係を再インストールしてください。
- `API キーが未設定です` → 設定ダイアログでキーを保存し、再試行します。
- それでも解決しない場合は `logs/` 配下のファイルを添えて開発チームへ報告してください。
