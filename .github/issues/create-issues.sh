#!/bin/bash
# GitHub Issues作成スクリプト
# PLANNED_FEATURES.mdの内容をGitHub Issuesとして起票します
#
# 使用方法:
# 1. GitHub CLI認証: gh auth login
# 2. スクリプト実行: bash .github/issues/create-issues.sh

set -e

echo "================================================"
echo "GitHub Issues作成スクリプト"
echo "================================================"

# リポジトリ情報確認
echo "リポジトリ情報を確認中..."
gh repo view --json nameWithOwner -q .nameWithOwner || {
  echo "Error: GitHub認証が必要です。'gh auth login' を実行してください。"
  exit 1
}

echo ""
echo "以下のIssuesを作成します:"
echo "- Epic: Slack Issue Agent 実装"
echo "- Feature: 会話型Issue収集"
echo "- Feature: Canvas統合"
echo "- Feature: Trello連携"
echo "- Infrastructure: AWS基盤構築"
echo "- Infrastructure: CloudWatch統合"
echo ""
read -p "続行しますか? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "中止しました。"
  exit 0
fi

echo ""
echo "================================================"
echo "Issues作成中..."
echo "================================================"

# Epic: Slack Issue Agent 実装
echo ""
echo "[1/6] Epic: Slack Issue Agent 実装"
gh issue create \
  --title "Epic: Slack Issue Agent 実装" \
  --label "epic" \
  --body "$(cat <<'EOF'
## 概要

**"Slackから離れずにIssueを起票する"** - 会話の流れを止めることなく、自然な対話でIssue情報を収集し、チームで確認してからTrelloに反映できる体験を提供します。

Slack上の会話から直接Issue起票まで完結し、ツール間の移動コストを最小化。AIエージェントが自然な会話で必要な情報を確実に収集し、Canvasでの共同編集により、Issue内容をチーム全体で確認・調整可能にします。

---

## アーキテクチャ

**マイクロサービス + AIエージェント** - Slack Events処理（Lambda）とAIエージェント実行（AgentCore）を分離し、スケーラビリティと保守性を両立

\`\`\`
┌─────────────┐
│   Slack     │
│  Workspace  │
└──────┬──────┘
       │ Events
       ↓
┌─────────────┐      ┌──────────────┐
│ AWS Lambda  │─────→│   Bedrock    │
│   Events    │      │  AgentCore   │
└─────────────┘      └──────┬───────┘
                            │
                            ↓
                     ┌──────────────┐
                     │ Slack Canvas │
                     │   + Trello   │
                     └──────────────┘
\`\`\`

---

## 主要コンポーネント

1. **会話型Issue収集** (#issue番号を後で追加)
2. **Canvas統合** (#issue番号を後で追加)
3. **Trello連携** (#issue番号を後で追加)
4. **AWS基盤構築** (#issue番号を後で追加)
5. **CloudWatch統合** (#issue番号を後で追加)

---

## 実装フェーズ

### Phase 1: インフラ基盤
- AWS CDK Stack実装（AgentCore, Lambda, API Gateway）
- Docker環境構築（AgentCore用）
- デプロイパイプライン構築
- CloudWatch統合

### Phase 2: Slack統合
- Slack Events APIエンドポイント実装
- Canvas API統合
- イベントハンドラ実装

### Phase 3: AIエージェント実装
- 会話フロー設計
- Strands Agentsツール実装
- Issue情報抽出ロジック

### Phase 4: Trello統合
- Trello API統合
- Canvas → Trelloマッピング
- エラーハンドリング

### Phase 5: エンドツーエンドテスト
- 統合テスト実装
- 負荷テスト
- セキュリティ監査

---

## 技術スタック

### 計画中
- **Framework**: Strands Agents (AI Agent), AWS CDK (Infrastructure)
- **Runtime**: AWS Bedrock AgentCore, AWS Lambda
- **AI Model**: Amazon Bedrock Claude Sonnet 4.5
- **Integrations**: Slack Canvas API, Trello API

---

## 参考

- [doc/PLANNED_FEATURES.md](../doc/PLANNED_FEATURES.md)
- [AWS Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Strands Agents](https://github.com/awslabs/strands-agents)
EOF
)"

echo "✓ Epic作成完了"

# Feature: 会話型Issue収集
echo ""
echo "[2/6] Feature: 会話型Issue収集"
gh issue create \
  --title "Feature: 会話型Issue収集" \
  --label "feature","phase-3" \
  --body "$(cat <<'EOF'
## 概要

Slackでチャット感覚でIssue情報をヒアリング

## 実装内容

- [ ] AIエージェントによる自然言語対話
- [ ] Issue情報の段階的な収集（タイトル、説明、優先度等）
- [ ] 不足情報の自動確認
- [ ] 会話フロー設計
- [ ] Strands Agentsツール実装
- [ ] Issue情報抽出ロジック

## 技術要件

- AWS Bedrock AgentCore統合
- Strands Agents実装
- Slack Events API統合

## 受入基準

- [ ] Slack上でエージェントと自然言語で対話できる
- [ ] 必須項目（タイトル、説明）を対話で収集できる
- [ ] オプション項目（優先度、担当者等）を対話で収集できる
- [ ] 不足情報がある場合、自動で確認質問される
- [ ] 収集した情報をCanvasに展開できる

## Phase

Phase 3: AIエージェント実装

## 参考

- [doc/PLANNED_FEATURES.md](../doc/PLANNED_FEATURES.md#1-会話型issue収集)
- [Strands Agents Documentation](https://github.com/awslabs/strands-agents)
EOF
)"

echo "✓ Feature: 会話型Issue収集 作成完了"

# Feature: Canvas統合
echo ""
echo "[3/6] Feature: Canvas統合"
gh issue create \
  --title "Feature: Canvas統合" \
  --label "feature","phase-2" \
  --body "$(cat <<'EOF'
## 概要

Markdown形式で構造化されたプレビューと共同編集

## 実装内容

- [ ] 収集したIssue情報のCanvasへの自動展開
- [ ] Markdown形式での構造化表示
- [ ] チームメンバーによる共同編集機能
- [ ] Canvas更新の即時反映
- [ ] Canvas最終版の取得

## 技術要件

- Slack Canvas API統合
- Markdown生成ロジック
- リアルタイム同期機構

## 受入基準

- [ ] 収集したIssue情報が自動でCanvasに展開される
- [ ] Canvasの内容がMarkdown形式で構造化されている
- [ ] 複数メンバーがCanvasを同時編集できる
- [ ] Canvas更新が即座に反映される
- [ ] 最終版のCanvas内容を取得できる

## Phase

Phase 2: Slack統合

## 参考

- [doc/PLANNED_FEATURES.md](../doc/PLANNED_FEATURES.md#2-canvas統合)
- [Slack Canvas API](https://api.slack.com/canvas)
EOF
)"

echo "✓ Feature: Canvas統合 作成完了"

# Feature: Trello連携
echo ""
echo "[4/6] Feature: Trello連携"
gh issue create \
  --title "Feature: Trello連携" \
  --label "feature","phase-4" \
  --body "$(cat <<'EOF'
## 概要

Canvas内容をTrelloカードとして自動作成

## 実装内容

- [ ] Canvas最終版の取得
- [ ] Trelloカード自動作成
- [ ] カスタムフィールドマッピング
- [ ] 添付ファイル同期（オプション）
- [ ] エラーハンドリング

## 技術要件

- Trello API統合
- Canvas → Trello変換ロジック
- エラーハンドリング

## 受入基準

- [ ] Canvas最終版を正確に取得できる
- [ ] Canvas内容からTrelloカードが自動作成される
- [ ] カスタムフィールド（優先度、担当者等）が正しくマッピングされる
- [ ] 添付ファイルがあれば同期される
- [ ] API エラー時に適切なエラーメッセージが表示される
- [ ] 作成したTrelloカードのURLがSlackに通知される

## Phase

Phase 4: Trello統合

## 参考

- [doc/PLANNED_FEATURES.md](../doc/PLANNED_FEATURES.md#3-自動trello連携)
- [Trello API](https://developer.atlassian.com/cloud/trello/rest/)
EOF
)"

echo "✓ Feature: Trello連携 作成完了"

# Infrastructure: AWS基盤構築
echo ""
echo "[5/6] Infrastructure: AWS基盤構築"
gh issue create \
  --title "Infrastructure: AWS基盤構築" \
  --label "infrastructure","phase-1" \
  --body "$(cat <<'EOF'
## 概要

AWS CDK v2によるインフラ構築（AgentCore, Lambda, API Gateway）

## 実装内容

### AWS Lambda (Events処理)
- [ ] Lambda関数実装（TypeScript）
- [ ] API Gateway統合
- [ ] Slack署名検証
- [ ] イベント振り分けロジック
- [ ] AgentCore呼び出し
- [ ] エラーハンドリング

### Bedrock AgentCore
- [ ] AgentCoreスタック（CDK）
- [ ] Dockerコンテナビルド
- [ ] デプロイパイプライン
- [ ] セッション管理
- [ ] メモリ管理

### セキュリティ
- [ ] IAM Role/Policy設定
- [ ] VPC設定（必要に応じて）
- [ ] Secrets Manager統合
- [ ] セキュリティグループ設定

### その他
- [ ] Docker環境構築（AgentCore用）
- [ ] デプロイパイプライン構築

## 技術要件

- AWS CDK v2 (TypeScript)
- Docker (ARM64)
- AWS Bedrock AgentCore
- AWS Lambda
- Amazon API Gateway

## 受入基準

- [ ] CDK deployが成功する
- [ ] Lambdaが正常にデプロイされる
- [ ] AgentCoreが正常にデプロイされる
- [ ] API GatewayエンドポイントがSlack Events APIに登録できる
- [ ] Slack Eventsが正常にLambdaに届く
- [ ] LambdaからAgentCoreを呼び出せる
- [ ] IAM権限が適切に設定されている
- [ ] セキュリティベストプラクティスに準拠している

## Phase

Phase 1: インフラ基盤

## 参考

- [doc/PLANNED_FEATURES.md](../doc/PLANNED_FEATURES.md#アーキテクチャ計画)
- [AWS Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
EOF
)"

echo "✓ Infrastructure: AWS基盤構築 作成完了"

# Infrastructure: CloudWatch統合
echo ""
echo "[6/6] Infrastructure: CloudWatch統合"
gh issue create \
  --title "Infrastructure: CloudWatch統合" \
  --label "infrastructure","phase-1","observability" \
  --body "$(cat <<'EOF'
## 概要

CloudWatch統合による詳細トレーシングと監視

## 実装内容

### ログ
- [ ] ログ集約（Lambda, AgentCore）
- [ ] 構造化ログ（JSON形式）
- [ ] ログレベル設定
- [ ] ログ保持期間設定

### メトリクス
- [ ] カスタムメトリクス収集
- [ ] Lambda実行時間・エラー率
- [ ] AgentCore実行時間・セッション数
- [ ] Slack API呼び出し回数
- [ ] Trello API呼び出し回数

### アラート
- [ ] エラー率アラート
- [ ] レイテンシアラート
- [ ] スロットリングアラート
- [ ] SNS通知設定

### トレーシング
- [ ] X-Ray統合
- [ ] 分散トレーシング
- [ ] パフォーマンス分析

## 技術要件

- Amazon CloudWatch Logs
- Amazon CloudWatch Metrics
- Amazon CloudWatch Alarms
- AWS X-Ray

## 受入基準

- [ ] 全コンポーネントのログがCloudWatchに集約される
- [ ] ログが構造化されており検索可能
- [ ] 主要メトリクスがダッシュボードで可視化される
- [ ] エラー発生時にアラートが通知される
- [ ] X-Rayでリクエストフローを追跡できる
- [ ] パフォーマンスボトルネックを特定できる

## Phase

Phase 1: インフラ基盤

## 参考

- [doc/PLANNED_FEATURES.md](../doc/PLANNED_FEATURES.md#observability)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [AWS X-Ray](https://docs.aws.amazon.com/xray/)
EOF
)"

echo "✓ Infrastructure: CloudWatch統合 作成完了"

echo ""
echo "================================================"
echo "✅ 全Issue作成完了！"
echo "================================================"
echo ""
echo "作成されたIssues:"
gh issue list --limit 10

echo ""
echo "次のステップ:"
echo "1. GitHub上でIssue番号を確認"
echo "2. Epic IssueにFeature/Infrastructure Issue番号を追記"
echo "3. マイルストーン設定（必要に応じて）"
echo "4. プロジェクトボード追加（必要に応じて）"
