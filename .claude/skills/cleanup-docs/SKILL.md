---
name: cleanup-docs
description: Archive existing doc/ directory to timestamped _archive/ location and create new concise README.md based on project Steering documents. Use when preparing repository for OSS publication, cleaning up documentation, or organizing project files for external sharing.
allowed-tools: [Read, Glob, Bash, Edit, Write]
---

# Cleanup Documentation for OSS Publication

## Instructions

このSkillは、プロジェクトのドキュメント構成をOSS公開に適した状態へ再編成します。既存の `doc/` ディレクトリをタイムスタンプ付きアーカイブへ移動し、Steeringドキュメントを基に簡潔な新規README.mdを作成します。

### Step 1: Load project context

プロジェクトの本質を理解するため、Steeringドキュメントを読み込みます:

1. **Read `.kiro/steering/product.md`**:
   - プロジェクトの目的、価値提案、主要機能を理解
   - Core Capabilitiesセクションを確認
   - Value Propositionを把握

2. **Read `.kiro/steering/tech.md`**:
   - 技術スタック(Python, TypeScript, AWS CDK, AgentCore等)を確認
   - Development Environmentセクションから mise, uv, Docker等の必須ツールを把握
   - Common Commandsセクションからセットアップコマンドを抽出

3. **Read `.kiro/steering/structure.md`**:
   - プロジェクト構造のパターンを理解
   - Directory Patternsセクションを確認

### Step 2: Generate timestamp and scan

アーカイブ先のタイムスタンプディレクトリを生成し、移動対象をスキャンします:

1. **Generate timestamp** (YYYYMMDD-HHMMSS format):

   ```bash
   TIMESTAMP=$(date +%Y%m%d-%H%M%S)
   echo "Timestamp: $TIMESTAMP"
   ```

2. **Use Glob tool to scan `doc/` directory**:
   - Pattern: `doc/**/*.md`
   - すべてのMarkdownファイルをリストアップ
   - ファイル数をカウント

3. **List all files that will be archived**:
   - スキャン結果を整形して表示

### Step 3: Show preview

ユーザーに移動対象とアクションを明示的にプレビュー表示します:

**プレビュー内容**:

```
📋 ドキュメントCleanupプレビュー

【移動対象】
- doc/ ディレクトリ (XX files) → _archive/YYYYMMDD-HHMMSS/doc/

【実行予定のアクション】
1. _archive/YYYYMMDD-HHMMSS/ ディレクトリを作成
2. doc/ → _archive/YYYYMMDD-HHMMSS/doc/ へ移動
3. .gitignore に _archive/ を追加 (まだ含まれていない場合)
4. 新規 README.md を作成 (Steeringベース、3セクション構成)

【注意】
- 既存のREADME.mdは _archive/ へ移動されます
- _archive/ は .gitignore に追加され、Git管理外となります
- 複数回実行した場合、過去のアーカイブは保持されます
```

### Step 4: Wait for user confirmation

**必ず**ユーザーの明示的な確認を待ちます:

- "実行しますか?" と尋ねる
- ユーザーが「実行して」「OK」「はい」等で承認した場合のみ次のステップへ進む
- ユーザーが「中止」「やめる」「いいえ」等で拒否した場合は操作を中止し、変更なしで終了

### Step 5: Execute cleanup steps

ユーザー承認後、以下の順序で実行します:

#### 5.1 Create archive directory

```bash
# Bash tool使用
mkdir -p "_archive/$TIMESTAMP"
```

#### 5.2 Move doc/ to archive

```bash
# Bash tool使用
mv doc/ "_archive/$TIMESTAMP/"
```

#### 5.3 Check and update .gitignore

1. **Read `.gitignore`** to check current contents
2. **Check if `_archive/` entry exists**:
   - 既に存在する場合 → スキップ(重複防止)
   - 存在しない場合 → Edit toolで追加

3. **Append to .gitignore** (存在しない場合のみ):
   ```
   # Cleanup: Archived documentation (not for OSS)
   _archive/
   ```

#### 5.4 Create new README.md

**Write tool使用**して新規 `README.md` をプロジェクトルートに作成します。

**Template Structure** (Steeringドキュメントベース):

````markdown
# Slack Issue Agent

## 概要

[product.mdのValue Propositionを2-3段落で記述]

Slack上でAIエージェントが自然な会話でIssue情報を収集し、Slack Canvasで視覚的に確認・編集した上で、Trelloボードに自動起票するシステムです。

## 主要機能

[product.mdのCore Capabilitiesから抽出]

- 会話型Issue収集: Slackでチャット感覚でIssue情報をヒアリング
- Canvas統合: Markdown形式で構造化されたプレビューと共同編集
- 自動Trello連携: Canvas内容をTrelloカードとして自動作成
- エンタープライズグレード基盤: AWS AgentCoreによるスケーラブルで安全な実行環境

## アーキテクチャ

[tech.mdのArchitectureセクションから簡潔に記述]

マイクロサービス + AIエージェント構成で、Slack Events処理（Lambda）とAIエージェント実行（AgentCore）を分離し、スケーラビリティと保守性を両立しています。

## 技術スタック

[tech.mdのCore Technologiesセクションから抽出]

- **Language**: Python 3.12+ (Agent), TypeScript (CDK & Lambda)
- **Framework**: Strands Agents (AI Agent), AWS CDK (Infrastructure)
- **Runtime**: AWS Bedrock AgentCore (Agent実行), AWS Lambda (Events処理)
- **AI Model**: Amazon Bedrock Claude Sonnet 4.5
- **IaC**: AWS CDK v2 (TypeScript)

### 必須ツール

[tech.mdのRequired Toolsセクションから抽出]

- **mise**: 統一されたランタイム管理（Node 22, Python 3.12）
- **uv**: 高速Python依存関係管理
- **Docker**: ARM64コンテナビルド（AgentCore用）
- **AWS CLI**: デプロイ・ログ確認

## セットアップ

[tech.mdのCommon Commandsセクションから抽出]

### クイックスタート

```bash
# Setup
mise run setup

# Test
mise run test

# CDK Deploy
cd cdk && npm run cdk deploy

# Agent Build
cd agent && docker buildx build --platform linux/arm64
```
````

### Dev Container (推奨)

VS CodeまたはCursorで開発する場合、Dev Containerを使用すると環境構築が自動化されます:

1. リポジトリをクローン
2. VS Code/Cursorで開く
3. "Dev Containers: Reopen in Container" を選択

## プロジェクト構造

[structure.mdのDirectory Patternsから主要パターンのみ記述]

```
slack-issue-agent/
├── cdk/                    # AWS CDK インフラ定義 (TypeScript)
├── agent/                 # AIエージェント実装 (Python)
├── .kiro/                 # Spec-Driven Development
│   ├── steering/          # プロジェクトメモリ
│   └── specs/             # 機能別仕様
└── .devcontainer/         # Dev Container設定
```

## ライセンス

このプロジェクトは実験用プロジェクトです。

````

**品質基準**:
- 行数: 200-300行を目安(簡潔に記述)
- 機密情報(API keys, credentials, internal URLs)が含まれないことを確認
- UTF-8エンコーディングで作成
- 一貫したMarkdownフォーマット

### Step 6: Validate results

実行結果を検証します:

1. **Verify archive structure**:
   ```bash
   # Bash tool使用
   ls -la "_archive/$TIMESTAMP/doc/"
````

- `_archive/YYYYMMDD-HHMMSS/doc/` が存在することを確認
- 元のdoc/ディレクトリと同じファイル数を確認

2. **Verify doc/ removal**:

   ```bash
   # Bash tool使用
   ls -la doc/ 2>&1 || echo "doc/ removed successfully"
   ```

   - `doc/` ディレクトリが存在しないことを確認

3. **Verify .gitignore update**:
   - Read toolで `.gitignore` を確認
   - `_archive/` エントリが含まれることを確認

4. **Verify new README.md**:
   - Read toolで新規 `README.md` を確認
   - 3セクション(概要、技術スタック、セットアップ)が存在することを確認
   - 200-300行程度であることを確認

### Step 7: Report completion

完了サマリーをユーザーに報告します:

```
✅ ドキュメントCleanup完了

【実行内容】
✓ _archive/YYYYMMDD-HHMMSS/ ディレクトリ作成完了
✓ doc/ (XX files) → _archive/YYYYMMDD-HHMMSS/doc/ へ移動完了
✓ .gitignore に _archive/ を追加 (またはスキップ)
✓ 新規 README.md 作成完了 (Slack Issue Agentの本質を簡潔に記述)

【アーカイブ先】
_archive/YYYYMMDD-HHMMSS/doc/

【次のステップ】
1. 新規 README.md の内容を確認
2. git status で変更内容を確認
3. 問題なければ git commit -m "docs: cleanup documentation for OSS publication"
```

エラーが発生した場合は、詳細なエラーメッセージと対処法を表示します。

## Important Notes

- このSkillは**複数回実行可能**です。実行の度に新しいタイムスタンプディレクトリが作成され、過去のアーカイブは保持されます
- `.gitignore` への `_archive/` 追加は初回のみ実行され、2回目以降はスキップされます
- 新規README.mdは**既存のREADME.mdを上書き**します(既存はアーカイブへ移動済み)
- **機密情報は含めないでください**: 新規README.md作成時、API keys, credentials, internal URLsを含めないよう注意してください
