# GitHub Issues作成ガイド

このディレクトリには、`doc/PLANNED_FEATURES.md`の内容をGitHub Issuesとして起票するスクリプトが含まれています。

## 前提条件

1. **GitHub CLI (gh) のインストール**

   ```bash
   # Dev Containerではインストール済み
   gh --version
   ```

2. **GitHub認証**

   ```bash
   gh auth login
   ```

   以下の手順に従って認証:
   - GitHubアカウント選択
   - HTTPS/SSH選択（HTTPS推奨）
   - 認証方法選択（Browser推奨）

## 使用方法

### 全Issue一括作成

```bash
bash .github/issues/create-issues.sh
```

### 個別Issue作成

個別にIssueを作成する場合は、`gh issue create`コマンドを使用:

```bash
gh issue create \
  --title "Issue タイトル" \
  --label "feature" \
  --body "Issue本文"
```

## 作成されるIssue一覧

スクリプトは以下の6つのIssuesを作成します:

### 1. Epic: Slack Issue Agent 実装

- **Label**: `epic`
- **内容**: プロジェクト全体の概要、アーキテクチャ、実装フェーズ

### 2. Feature: 会話型Issue収集

- **Label**: `feature`, `phase-3`
- **内容**: AIエージェントによる自然言語対話、Issue情報収集

### 3. Feature: Canvas統合

- **Label**: `feature`, `phase-2`
- **内容**: Slack Canvas統合、Markdown表示、共同編集

### 4. Feature: Trello連携

- **Label**: `feature`, `phase-4`
- **内容**: Trelloカード自動作成、Canvas→Trelloマッピング

### 5. Infrastructure: AWS基盤構築

- **Label**: `infrastructure`, `phase-1`
- **内容**: CDK, Lambda, AgentCore, セキュリティ設定

### 6. Infrastructure: CloudWatch統合

- **Label**: `infrastructure`, `phase-1`, `observability`
- **内容**: ログ、メトリクス、アラート、X-Ray統合

## Issue作成後の作業

### 1. Epic Issueの更新

Epic IssueにFeature/Infrastructure Issue番号を追記:

```markdown
## 主要コンポーネント

1. **会話型Issue収集** (#2)
2. **Canvas統合** (#3)
3. **Trello連携** (#4)
4. **AWS基盤構築** (#5)
5. **CloudWatch統合** (#6)
```

### 2. マイルストーン設定（オプション）

```bash
# マイルストーン作成
gh api repos/:owner/:repo/milestones -f title="v1.0.0 PoC" -f description="PoC完成"

# Issueにマイルストーン設定
gh issue edit 1 --milestone "v1.0.0 PoC"
```

### 3. プロジェクトボード追加（オプション）

```bash
# プロジェクト一覧表示
gh project list

# Issueをプロジェクトに追加
gh project item-add <PROJECT_NUMBER> --owner <OWNER> --url https://github.com/<OWNER>/<REPO>/issues/1
```

## ラベル管理

必要に応じて追加のラベルを作成:

```bash
# ラベル作成
gh label create "phase-1" --description "Phase 1: インフラ基盤" --color "0E8A16"
gh label create "phase-2" --description "Phase 2: Slack統合" --color "1D76DB"
gh label create "phase-3" --description "Phase 3: AIエージェント実装" --color "5319E7"
gh label create "phase-4" --description "Phase 4: Trello統合" --color "E99695"
gh label create "epic" --description "Epic Issue" --color "D93F0B"
gh label create "feature" --description "Feature" --color "0075CA"
gh label create "infrastructure" --description "Infrastructure" --color "FEF2C0"
gh label create "observability" --description "Observability" --color "FBCA04"
```

## トラブルシューティング

### 認証エラー

```bash
# 認証状態確認
gh auth status

# 再認証
gh auth login
```

### リポジトリ情報が取得できない

```bash
# リポジトリ情報確認
gh repo view

# リモートURL確認
git remote -v
```

### Issue作成失敗

- GitHub上で手動作成を試す
- ラベルが存在しない場合は、上記「ラベル管理」を参照

## 参考

- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [gh issue create](https://cli.github.com/manual/gh_issue_create)
- [doc/PLANNED_FEATURES.md](../../doc/PLANNED_FEATURES.md)
