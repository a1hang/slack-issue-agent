# Project Structure

## Organization Philosophy

**関心の分離 + デプロイ境界**: インフラ定義（`cdk/`）、エージェント実装（`agent/`）、Lambda関数（`lambda/`）を明確に分離し、独立したビルド・デプロイサイクルを実現

## Directory Patterns

### Infrastructure (`/cdk/`)

**Location**: `/cdk/`
**Purpose**: AWS CDKによるインフラ定義（TypeScript）
**Example**:

- `bin/`: CDKアプリエントリーポイント
- `lib/`: Stack定義（AgentCore, API Gateway, etc.）
- `package.json`: Node.js 22+依存関係

### Agent (`/agent/`)

**Location**: `/agent/`
**Purpose**: Strands AgentsによるAIエージェント実装（Python）
**Example**:

- `src/slack_issue_agent/`: エージェントロジック
- `tests/`: pytest テスト（環境検証、統合テスト、セキュリティテスト）
- `pyproject.toml`: Python 3.12+依存関係
- `Dockerfile`: ARM64コンテナ定義（AgentCore用）

**Test Organization Pattern**:

- 環境検証: `test_tool_versions.py`, `test_dependencies.py`, `test_cdk_build_lint.py`
- AWS統合: `test_aws_connection.py`, `test_cdk_bootstrap.py`, `test_assume_role.py`
- セキュリティ: `test_git_secrets.py`, `test_git_secrets_blocking.py`
- 統合テスト: `test_integration.py`, `test_slack_client.py`

### Lambda Functions (`/lambda/`)

**Location**: `/lambda/`
**Purpose**: Slack Events Handler等のLambda関数
**Example**: 現在は空（CDK inline implementationを想定）

### Documentation (`/doc/`)

**Location**: `/doc/`
**Purpose**: プロジェクト詳細ドキュメント
**Example**:

- `README.md`: プロジェクト概要
- `PROJECT_OVERVIEW.md`: 技術詳細
- `IMPLEMENTATION_GUIDE.md`: 実装ガイド

### Kiro Specs (`/.kiro/`)

**Location**: `/.kiro/`
**Purpose**: Spec-Driven Development設定とステアリング
**Example**:

- `steering/`: プロジェクトメモリ（このファイル含む）
- `specs/`: 機能別仕様定義
- `settings/`: Kiroテンプレートとルール

## Naming Conventions

- **Directories**: kebab-case (`slack-issue-agent`, `agent-core`)
- **Python Modules**: snake_case (`slack_issue_agent`)
- **TypeScript Files**: kebab-case (`agentcore-stack.ts`)
- **Python Files**: snake_case (`canvas_tool.py`)

## Import Organization

### Python

```python
# Standard library
import os
from typing import Any

# Third-party
from strands_agents import Agent
from slack_sdk import WebClient

# Local
from slack_issue_agent.tools import CanvasTool
```

### TypeScript (CDK)

```typescript
// AWS CDK
import * as cdk from "aws-cdk-lib";
import * as agentcore from "@aws-cdk/aws-bedrock-agentcore-alpha";

// Local
import { AgentCoreStack } from "./lib/agentcore-stack";
```

## Code Organization Principles

- **単一責任**: 各ディレクトリは明確な境界を持つ（infra, agent, lambda）
- **疎結合**: Agent実装はCDK定義に依存せず、独立してテスト・開発可能
- **デプロイ独立性**: CDKデプロイとAgentコンテナビルドは別プロセス

---

_Document patterns, not file trees. New files following patterns shouldn't require updates_
