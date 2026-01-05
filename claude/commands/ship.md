---
description: Lint, commit, push, and monitor GitHub Actions
allowed-tools: Bash, Read, Edit, Glob, Grep, Write
---

以下の手順で変更をデプロイしてください：

## 1. Lint チェック
- 現在のディレクトリを確認し、適切なアプリディレクトリで `npm run lint` を実行
- エラーがある場合は修正を試みる
- 既存のwarningは無視してOK

## 2. Commit & Push
- `git status` で変更を確認
- 変更内容に応じた日本語のコミットメッセージを作成
- `git add` で必要なファイルをステージング（.pycache等は除外）
- `git commit` でコミット
- `git push` でリモートにプッシュ

## 3. GitHub Actions 監視
- `gh run list --branch <current-branch> --limit 1` で最新のワークフローを確認
- `gh run watch <run-id> --exit-status` でワークフローを監視
- 正常終了したら結果を報告
- 異常終了した場合：
  1. `gh run view <run-id> --log-failed` でエラーログを確認
  2. 原因を調査して修正を試みる
  3. 修正後、再度 commit & push して監視を続ける

## 注意事項
- コミットメッセージは日本語で簡潔に
- 直感的でない変更やworkaroundの場合は背景も説明する
