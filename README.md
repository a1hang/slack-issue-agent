# Slack Issue Agent

**PoC (Proof of Concept)** - Slack上でAIエージェントが自然な会話でIssue情報を収集し、Slack Canvasで視覚的に確認・編集した上で、Trelloボードに自動起票するシステムの概念検証プロジェクトです。

**⚠️ 注意**: このプロジェクトは現在PoC段階であり、主要機能はまだ実装されていません。開発計画は [GitHub Issues](https://github.com/a1hang/slack-issue-agent/issues) を参照してください。

---

## 開発環境

### 必須ツール

- **mise**: 統一されたランタイム管理（Node 22, Python 3.12）
- **uv**: 高速Python依存関係管理
- **pre-commit**: Git hooks自動化（lint/format/型チェック）
- **Docker**: ARM64コンテナビルド（AgentCore用）
- **AWS CLI**: デプロイ・ログ確認

### セットアップ

#### Dev Container (推奨)

VS CodeまたはCursorで開発する場合、Dev Containerを使用すると環境構築が自動化されます:

1. リポジトリをクローン
2. VS Code/Cursorで開く
3. "Dev Containers: Reopen in Container" を選択

#### ローカル環境

```bash
# Setup
mise run setup

# Test
mise run test
```

---

## プロジェクト構造

```
slack-issue-agent/
├── agent/                 # AIエージェント実装 (Python)
│   ├── src/               # エージェントコード
│   ├── tests/             # テスト
│   └── pyproject.toml     # Python依存関係
├── .kiro/                 # Spec-Driven Development
│   ├── steering/          # プロジェクトメモリ
│   └── settings/          # Kiroテンプレート・ルール
└── .devcontainer/         # Dev Container設定
```

---

## 開発ガイドライン

### コーディング規約

**Python**:

- ruff による静的解析・フォーマット
- mypy による型チェック（strict mode）
- Python 3.12+ strict typing
- line-length=100

**TypeScript**:

- strict mode有効
- ESLint + Prettier
- Node.js 22+

### pre-commit

Git commitの前に自動で品質チェックが実行されます:

**自動実行される項目**:

- **Ruff**: Python lint + format
- **mypy**: Python型チェック（strict mode）
- **Prettier**: TypeScript/JavaScript/JSON/YAML/Markdown format
- **ESLint**: TypeScript/JavaScript lint
- **git-secrets**: AWS credentials検出
- **汎用チェック**: YAML/JSON構文、trailing whitespace、merge conflict等

**手動実行**:

```bash
# 全ファイルチェック
agent/.venv/bin/pre-commit run --all-files

# 特定のhookのみ実行
agent/.venv/bin/pre-commit run ruff --all-files
agent/.venv/bin/pre-commit run mypy --all-files
```

**初回セットアップ**（Dev Containerでは自動実行）:

```bash
uv pip install pre-commit
agent/.venv/bin/pre-commit install
```

### テスト

```bash
# Python tests
cd agent
pytest

# TypeScript tests (未実装)
cd cdk
npm test
```

---

## デプロイ

デプロイ手順の詳細は [cdk/README.md](cdk/README.md) を参照してください。

### クイックスタート

1. **SSM Parameter Store 設定** - Slack/Trello認証情報を登録
2. **CDK デプロイ** - `cd cdk && cdk deploy --all`
3. **Slack App 設定** - Lambda Function URL を Event Subscriptions に登録

```bash
# デプロイ
cd cdk
npm install
cdk deploy --all

# Lambda Function URL 取得
aws cloudformation describe-stacks \
  --stack-name SlackIssueAgentLambdaStack \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text \
  --region ap-northeast-1
```

---

## 技術スタック

### 実装済み

- **Language**: Python 3.12+
- **Code Quality**:
  - **Ruff**: Linter + Formatter（黒・isort・flake8統合）
  - **mypy**: 型チェッカー（strict mode）
  - **pre-commit**: Git hooks自動化
- **Package Manager**: uv（高速Python依存関係管理）
- **Runtime Manager**: mise（Node 22, Python 3.12統一管理）
- **Development**: Dev Container, Docker

### 計画中

詳細は [GitHub Issues](https://github.com/a1hang/slack-issue-agent/issues) を参照してください。

- **Framework**: Strands Agents (AI Agent), AWS CDK (Infrastructure)
- **Runtime**: AWS Bedrock AgentCore, AWS Lambda
- **AI Model**: Amazon Bedrock Claude Sonnet 4.5
- **Integrations**: Slack Canvas API, Trello API

---

## ライセンス

このプロジェクトは実験用プロジェクトです。

### 使用しているオープンソースソフトウェア

このプロジェクトは以下のオープンソースソフトウェアを使用しています:

- **[gotalab/cc-sdd](https://github.com/gotalab/cc-sdd)** (MIT License)
  - Spec-Driven Development ワークフロー (`.claude/commands/kiro/`, `.kiro/settings/`)
  - 詳細は `NOTICE` ファイルおよび各ディレクトリの `LICENSE` ファイルを参照してください

---

## 参考リンク

- [GitHub Issues](https://github.com/a1hang/slack-issue-agent/issues) - 開発計画・進捗
- [AWS Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Strands Agents](https://github.com/awslabs/strands-agents)
- [Slack Canvas API](https://api.slack.com/canvas)
- [Trello API](https://developer.atlassian.com/cloud/trello/rest/)
