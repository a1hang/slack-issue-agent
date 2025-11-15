# Technology Stack

## Architecture

**マイクロサービス + AIエージェント** - Slack Events処理（Lambda）とAIエージェント実行（AgentCore）を分離し、スケーラビリティと保守性を両立

## Core Technologies

- **Language**: Python 3.12+ (Agent & Lambda), TypeScript (CDK)
- **Framework**: Strands Agents (AI Agent), AWS CDK (Infrastructure)
- **Runtime**: AWS Bedrock AgentCore (Agent実行), AWS Lambda (Events処理)
- **AI Model**: Amazon Bedrock Claude Sonnet 4.5
- **IaC**: AWS CDK v2 (TypeScript)

## Key Libraries

### Infrastructure (CDK)

- `@aws-cdk/aws-bedrock-agentcore-alpha`: AgentCore構築
- `aws-cdk-lib`: 標準AWSリソース定義

### Agent (Python)

- `strands-agents`: エージェントフレームワーク
- `slack-sdk`: Slack API操作（Canvas含む）
- `httpx`: 非同期HTTP通信（Trello API）

## Development Standards

### Type Safety

- **Python**: ruff による静的解析、Python 3.12+ strict typing
- **TypeScript**: strict mode有効、ESLint + Prettier

### Code Quality

- **Python**: ruff format, line-length=100
- **TypeScript**: ESLint + Prettier, Node.js 22+

### Testing

- **Python**: pytest（単体・統合テスト）
- **TypeScript**: Jest
- **Environment Verification**: ツールバージョン、依存関係、ビルド、AWS接続の自動検証テスト

## Development Environment

### Required Tools

- **mise**: 統一されたランタイム管理（Node 22, Python 3.12）
- **uv**: 高速Python依存関係管理
- **Docker**: ARM64コンテナビルド（AgentCore用）
- **AWS CLI**: デプロイ・ログ確認
- **git-secrets**: 機密情報コミット防止（AWS Keys, Slack/Trello Tokens）

### Common Commands

```bash
# Setup: mise run setup
# Test: mise run test
# CDK Deploy: cd cdk && npm run cdk deploy
# Agent Build: cd agent && docker buildx build --platform linux/arm64
```

## Key Technical Decisions

### AgentCoreの採用理由

- **長時間実行**: 最大8時間のセッション維持（複雑な対話フロー対応）
- **マネージドメモリ**: 会話履歴とコンテキストの自動管理
- **Observability**: CloudWatch統合による詳細トレーシング

### Strands Agentsの選択

- AWS推奨Pythonエージェントフレームワーク
- AgentCoreとのネイティブ統合
- シンプルなツール定義とデプロイモデル

### Block Kit非採用

Canvas統合に注力し、実装複雑度を低減。Canvasが編集可能な「単一の真実の情報源」として機能

### Docker-outside-of-docker採用

Dev Containerで `docker-outside-of-docker` Feature を使用し、ホストのDockerソケットを共有。Docker-in-Dockerより軽量でビルドキャッシュ共有可能

---

_Document standards and patterns, not every dependency_
