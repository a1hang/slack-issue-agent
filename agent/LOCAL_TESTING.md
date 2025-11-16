# Local Testing Guide for Slack Issue Agent

このガイドでは、AgentCore エントリーポイントをローカル環境でテストする方法を説明します。

## 前提条件

- Python 3.12+
- uv (Python dependency manager)
- AWS認証情報 (Bedrock Claude Sonnet 4.5 へのアクセス権限)

## セットアップ

```bash
# 依存関係のインストール
cd agent
uv sync
```

## ローカル実行

### 方法 1: mise タスク (推奨)

```bash
# プロジェクトルートから実行
mise run agent:local
```

### 方法 2: uv run

```bash
# agent/ ディレクトリから実行
cd agent
uv run python -m slack_issue_agent.agentcore_app
```

### 方法 3: 直接実行

```bash
cd agent/src
python -m slack_issue_agent.agentcore_app
```

いずれの方法でも、HTTP サーバーが `http://localhost:8080` で起動します。

## エンドポイント

### POST /invocations

エージェントを呼び出すメインエンドポイント。

**リクエスト形式:**

```json
{
  "prompt": "ユーザーからのメッセージ"
}
```

**レスポンス形式:**

```json
{
  "result": "エージェントからの応答"
}
```

### GET /ping

ヘルスチェックエンドポイント。

**レスポンス:**

```json
{
  "status": "healthy"
}
```

## テスト方法

### curl でのテスト

```bash
# ヘルスチェック
curl http://localhost:8080/ping

# サンプルペイロードでエージェント呼び出し
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d @test-payloads/sample-invocation.json

# カスタムプロンプト
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Issueを作成したいです"}'
```

### サンプルペイロード

`test-payloads/` ディレクトリに以下のサンプルが用意されています:

- `sample-invocation.json` - 基本的な会話開始
- `slack-mention-event.json` - Slack メンション形式
- `empty-prompt.json` - 空のプロンプト (エラーハンドリングテスト)

## Docker でのローカルテスト

```bash
# Docker イメージをビルド
mise run agent:build

# コンテナを起動
docker run --platform linux/arm64 -p 8080:8080 \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
  -e AWS_REGION="$AWS_REGION" \
  slack-issue-agent:latest

# 別のターミナルでテスト
curl http://localhost:8080/ping
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!"}'
```

## トラブルシューティング

### ポート 8080 が使用中

別のプロセスが 8080 を使用している場合:

```bash
# ポートを使用しているプロセスを確認
lsof -i :8080

# プロセスを停止するか、別のポートを使用
PORT=8081 uv run python -m slack_issue_agent.agentcore_app
```

### AWS 認証エラー

```bash
# AWS 認証情報を確認
aws sts get-caller-identity

# 認証情報が正しく設定されているか確認
env | grep AWS_
```

### Bedrock モデルアクセスエラー

Claude Sonnet 4.5 モデルへのアクセス権限を確認:

```bash
aws bedrock list-foundation-models \
  --region ap-northeast-1 \
  --query 'modelSummaries[?contains(modelId, `claude-sonnet-4-5`)]'
```

## 次のステップ

ローカルテストが成功したら:

1. Docker イメージをビルド: `mise run agent:build`
2. ECR にプッシュ: `mise run agent:push`
3. CDK でデプロイ: `cd ../cdk && npm run cdk deploy`

## 参考資料

- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [Bedrock AgentCore Deployment Guide](https://aws.github.io/bedrock-agentcore-starter-toolkit/)
