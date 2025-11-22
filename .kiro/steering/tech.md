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

- `aws-cdk-lib` (2.227.0): 標準AWSリソース定義
- `@aws-cdk/aws-bedrock-agentcore-alpha` (2.224.0): AgentCore構築
- `cdk-ecr-deployment`: DockerImageAssetからECRリポジトリへのイメージデプロイ

### Lambda (Python)

- 依存関係は `lib/python/` ディレクトリにインストール
- `sys.path` 設定でランタイムから参照
- `uv pip install --target lib/python/` でインストール

### Agent (Python)

- `strands-agents`: エージェントフレームワーク
- `bedrock-agentcore`: AgentCore Runtime統合
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
- **Local Testing**: AgentCore HTTP サーバー（localhost:8080）でのローカルテスト

## Development Environment

### Required Tools

- **mise**: 統一されたランタイム管理（Node 22, Python 3.12）
- **uv**: 高速Python依存関係管理
- **Docker**: ARM64コンテナビルド（AgentCore用）
- **AWS CLI**: デプロイ・ログ確認
- **git-secrets**: 機密情報コミット防止（AWS Keys, Slack/Trello Tokens）

### Common Commands

```bash
# Setup
mise run setup

# Test
mise run test

# Local Testing (AgentCore HTTP server on localhost:8080)
mise run agent:local

# Docker Build & Deployment
mise run agent:build   # Build ARM64 image locally
mise run agent:push    # Build and push to ECR

# CDK Deployment (global CLI)
cd cdk && cdk deploy --all
```

**Note**: CDK CLIはグローバルインストール (`npm install -g aws-cdk@latest`) を推奨。現在v2.1033.0を使用。

**デプロイ前提条件**: SSM Parameter Store設定（詳細は DEPLOYMENT_GUIDE.md 参照）

## Key Technical Decisions

### AgentCoreの採用理由

- **長時間実行**: 最大8時間のセッション維持（複雑な対話フロー対応）
- **マネージドメモリ**: 会話履歴とコンテキストの自動管理
- **Observability**: CloudWatch統合による詳細トレーシング

### Strands Agentsの選択

- AWS推奨Pythonエージェントフレームワーク
- AgentCoreとのネイティブ統合
- シンプルなツール定義とデプロイモデル

### Geographic Inference Profile (Japan)

**決定**: Claude Sonnet 4.5 の日本地域推論プロファイル `jp.anthropic.claude-sonnet-4-5-20250929-v1:0` を採用

**理由**:

- **Cross-Region Inference System (CRIS)**: 東京（ap-northeast-1）と大阪（ap-northeast-3）間で自動ルーティング
- **データローカライゼーション**: すべてのデータが日本国内に留まり、コンプライアンス要件を満たす
- **可用性向上**: リージョン障害時の自動フェイルオーバー

### Block Kit非採用

Canvas統合に注力し、実装複雑度を低減。Canvasが編集可能な「単一の真実の情報源」として機能

### Docker-outside-of-docker採用

Dev Containerで `docker-outside-of-docker` Feature を使用し、ホストのDockerソケットを共有。Docker-in-Dockerより軽量でビルドキャッシュ共有可能

### AgentCore Container Deployment採用

**決定**: ECRコンテナデプロイを採用（当初のZipデプロイから変更）

**理由**:

- AWS CDK `@aws-cdk/aws-bedrock-agentcore-alpha` v2.224.0時点でZipデプロイ未対応
- コンテナベースのデプロイパターンが充実
- ARM64イメージビルド（`docker buildx`）によるAgentCore Runtime最適化

**将来の検討**: CDK Zipサポート追加時の移行（Issue #8で管理）

### ECRDeployment パターン

**決定**: `cdk-ecr-deployment` を使用してDockerImageAssetから専用ECRリポジトリにイメージをコピー

**理由**:

- **イメージ管理**: 自分で管理するECRリポジトリでタグとライフサイクルを制御
- **デプロイ順序**: `node.addDependency()` で AgentCore Runtime がイメージ存在後に作成されることを保証
- **RETAIN ポリシー**: スタック削除時もECRリポジトリを保持（誤削除防止）

### Multi-stage Docker Build

**パターン**: uvのARM64公式イメージを使用した2段階ビルド

**Stage 1 (builder)**: 依存関係インストール（uv sync）
**Stage 2 (runtime)**: 最小限のプロダクションイメージ（.venvとソースコードのみ）

**メリット**:

- イメージサイズの最小化（ビルドツール不要）
- uv による高速依存関係インストール
- セキュリティ強化（不要なツール削除）

---

_Document standards and patterns, not every dependency_
_Updated: 2025-11-22 - Added cdk-ecr-deployment, Lambda lib/python pattern, global CDK CLI_
