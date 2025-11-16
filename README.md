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

### 前提条件

1. **AWS CLI設定**:

   ```bash
   aws configure
   # Region: ap-northeast-1 (東京リージョン)
   # Output: json
   ```

2. **Node.js 22+とAWS CDKのインストール**:
   ```bash
   mise install nodejs@22
   npm install -g aws-cdk
   cdk --version  # v2.x を確認
   ```

### ステップ 1: SSM Parameter Store の設定

AWS CDKデプロイの前に、以下の4つのSSM Parameter Storeパラメータを作成する必要があります。

**重要**: これらのパラメータが存在しない場合、CDKデプロイは失敗します。

#### 必要なパラメータ

1. **Slack Bot Token** (`/slack-issue-agent/slack/bot-token`)
2. **Slack Signing Secret** (`/slack-issue-agent/slack/signing-secret`)
3. **Trello API Key** (`/slack-issue-agent/trello/api-key`)
4. **Trello Token** (`/slack-issue-agent/trello/token`)

#### AWS CLIコマンド

```bash
# 1. Slack Bot Token (xoxb- で始まるトークン)
aws ssm put-parameter \
  --name "/slack-issue-agent/slack/bot-token" \
  --value "xoxb-YOUR-SLACK-BOT-TOKEN" \
  --type "SecureString" \
  --description "Slack Bot User OAuth Token" \
  --region ap-northeast-1

# 2. Slack Signing Secret (Slack App設定画面から取得)
aws ssm put-parameter \
  --name "/slack-issue-agent/slack/signing-secret" \
  --value "YOUR-SLACK-SIGNING-SECRET" \
  --type "SecureString" \
  --description "Slack App Signing Secret for request verification" \
  --region ap-northeast-1

# 3. Trello API Key (https://trello.com/app-key から取得)
aws ssm put-parameter \
  --name "/slack-issue-agent/trello/api-key" \
  --value "YOUR-TRELLO-API-KEY" \
  --type "SecureString" \
  --description "Trello API Key" \
  --region ap-northeast-1

# 4. Trello Token (Trello API Key画面で生成)
aws ssm put-parameter \
  --name "/slack-issue-agent/trello/token" \
  --value "YOUR-TRELLO-TOKEN" \
  --type "SecureString" \
  --description "Trello User Token" \
  --region ap-northeast-1
```

#### パラメータ設定の確認

```bash
# 作成されたパラメータを確認 (値は表示されない)
aws ssm describe-parameters \
  --parameter-filters "Key=Name,Values=/slack-issue-agent/" \
  --region ap-northeast-1

# 特定のパラメータ値を確認 (復号化して表示)
aws ssm get-parameter \
  --name "/slack-issue-agent/slack/bot-token" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text \
  --region ap-northeast-1
```

#### セキュリティ設定

**SecureString タイプ**:

- すべてのパラメータは `SecureString` タイプで作成されます
- AWS KMS (デフォルトキー `alias/aws/ssm`) による自動暗号化
- Standard tier (無料) を使用し、コスト最適化

**KMS 暗号化**:

```bash
# カスタムKMSキーを使用する場合（オプション）
aws ssm put-parameter \
  --name "/slack-issue-agent/slack/bot-token" \
  --value "xoxb-YOUR-SLACK-BOT-TOKEN" \
  --type "SecureString" \
  --key-id "alias/your-custom-kms-key" \
  --description "Slack Bot User OAuth Token" \
  --region ap-northeast-1
```

#### CDK デプロイ時のエラーメッセージ例

パラメータが存在しない場合、CDK デプロイは以下のようなエラーで失敗します:

```
❌  SlackIssueAgentSharedStack failed: Error: Parameter /slack-issue-agent/slack/bot-token not found
    at ParameterNotFound: /slack-issue-agent/slack/bot-token (Service: SSM; Status Code: 400; Error Code: ParameterNotFound)

Required SSM Parameters:
  - /slack-issue-agent/slack/bot-token
  - /slack-issue-agent/slack/signing-secret
  - /slack-issue-agent/trello/api-key
  - /slack-issue-agent/trello/token

Please create these parameters using the AWS CLI commands in the README.
```

### ステップ 2: Dockerイメージのビルドとプッシュ

AgentCore用のDockerイメージをビルドし、ECRにプッシュします。

```bash
# ECRリポジトリURIを取得（CDKデプロイ後）
export ECR_REPO_URI=$(aws cloudformation describe-stacks \
  --stack-name SlackIssueAgentAgentCoreStack \
  --query 'Stacks[0].Outputs[?OutputKey==`AgentRepositoryUri`].OutputValue' \
  --output text \
  --region ap-northeast-1)

# ECRログイン
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin $ECR_REPO_URI

# ARM64イメージをビルド
cd agent
docker buildx build --platform linux/arm64 -t slack-issue-agent:latest .

# タグ付けとプッシュ
docker tag slack-issue-agent:latest $ECR_REPO_URI:latest
docker push $ECR_REPO_URI:latest
```

**miseタスクを使用する場合**:

```bash
mise run docker:build-and-push
```

### ステップ 3: CDK デプロイ

```bash
cd cdk

# CDK依存関係をインストール
npm install

# CloudFormationテンプレート生成
cdk synth

# 全スタックをデプロイ
cdk deploy --all

# または個別にデプロイ
cdk deploy SlackIssueAgentSharedStack
cdk deploy SlackIssueAgentAgentCoreStack
cdk deploy SlackIssueAgentLambdaStack
```

### ステップ 4: Lambda Function URL の取得と設定

```bash
# Lambda Function URLを取得
aws cloudformation describe-stacks \
  --stack-name SlackIssueAgentLambdaStack \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text \
  --region ap-northeast-1
```

このURLを Slack App Dashboard の **Event Subscriptions** → **Request URL** に設定します。

### ステップ 5: 動作確認

```bash
# CloudWatch Logsでログ確認
aws logs tail /aws/lambda/SlackIssueAgent-SlackEventsHandler --follow --region ap-northeast-1

# Slackでボットにメンション
# 例: @YourBot こんにちは
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
