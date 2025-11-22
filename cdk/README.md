# CDK Infrastructure

Slack Issue Agent の AWS インフラストラクチャを定義する AWS CDK プロジェクト。

## スタック構成

```
SharedStack (S3 Bucket)
    ↓
AgentCoreStack (ECR Repository + AgentCore Runtime + IAM Role)
    ↓
LambdaStack (Lambda Function + Function URL + IAM Role)
```

- **SharedStack**: S3 Bucket（Agent Code用、RETAIN）
- **AgentCoreStack**: ECR Repository、AgentCore Runtime、IAM Role
- **LambdaStack**: Lambda Function、Function URL、IAM Role

## 前提条件

### 1. SSM Parameter Store の設定

CDKデプロイ前に、以下の4つのパラメータを作成してください:

```bash
# Slack Bot Token
aws ssm put-parameter \
  --name "/slack-issue-agent/slack/bot-token" \
  --value "xoxb-YOUR-TOKEN" \
  --type "SecureString" \
  --region ap-northeast-1

# Slack Signing Secret
aws ssm put-parameter \
  --name "/slack-issue-agent/slack/signing-secret" \
  --value "YOUR-SECRET" \
  --type "SecureString" \
  --region ap-northeast-1

# Trello API Key
aws ssm put-parameter \
  --name "/slack-issue-agent/trello/api-key" \
  --value "YOUR-API-KEY" \
  --type "SecureString" \
  --region ap-northeast-1

# Trello Token
aws ssm put-parameter \
  --name "/slack-issue-agent/trello/token" \
  --value "YOUR-TOKEN" \
  --type "SecureString" \
  --region ap-northeast-1
```

確認:

```bash
aws ssm describe-parameters \
  --parameter-filters "Key=Name,Values=/slack-issue-agent/" \
  --region ap-northeast-1
```

### 2. CDK Bootstrap

```bash
cdk bootstrap aws://ACCOUNT_ID/ap-northeast-1
```

## デプロイ

### 全スタックデプロイ

```bash
cd cdk
npm install
cdk deploy --all
```

CDKが自動的に:

1. ECR Repository 作成
2. Docker イメージビルド (ARM64)
3. ECR へプッシュ
4. AgentCore Runtime 作成
5. Lambda Function + Function URL 作成

初回デプロイ: 約5-10分

### 個別デプロイ

```bash
cdk deploy SlackIssueAgentSharedStack
cdk deploy SlackIssueAgentAgentCoreStack
cdk deploy SlackIssueAgentLambdaStack
```

## デプロイ後の設定

### Lambda Function URL の取得

```bash
aws cloudformation describe-stacks \
  --stack-name SlackIssueAgentLambdaStack \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text \
  --region ap-northeast-1
```

### Slack App 設定

1. [Slack API Dashboard](https://api.slack.com/apps) を開く
2. **Event Subscriptions** → **Enable Events** をオン
3. **Request URL** に Lambda Function URL を設定
4. **Subscribe to bot events** で `app_mention` を追加
5. **Save Changes**

## 動作確認

```bash
# Lambda ログ
aws logs tail /aws/lambda/SlackIssueAgent-SlackEventsHandler --follow --region ap-northeast-1

# AgentCore ログ
aws logs tail /aws/bedrock/agentcore/SlackIssueAgentRuntime --follow --region ap-northeast-1
```

## スタック削除

```bash
cdk destroy --all
```

**注意**:

- ECR Repository は RETAIN ポリシー（手動削除が必要）
- S3 Bucket は RETAIN ポリシー（手動削除が必要）
- SSM Parameter は削除されない

## トラブルシューティング

### "Invalid signature" エラー

Slack Signing Secret を確認:

```bash
aws ssm get-parameter \
  --name "/slack-issue-agent/slack/signing-secret" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text
```

### "Parameter not found" エラー

SSM パラメータが作成されているか確認（前提条件セクション参照）

### "Image not found" エラー

ECRDeployment の完了を待ってから AgentCore Runtime が作成されるよう、CDK内で依存関係を設定済み。
問題が続く場合は再デプロイ:

```bash
cdk deploy SlackIssueAgentAgentCoreStack
```

## CDK コマンド

- `cdk synth` - CloudFormation テンプレート生成
- `cdk diff` - 変更差分確認
- `cdk deploy --all` - 全スタックデプロイ
- `cdk destroy --all` - 全スタック削除

## 技術的決定

### グローバル CDK CLI

`npm install -g aws-cdk@latest` でグローバルインストールを推奨。

### cdk-ecr-deployment

DockerImageAsset から専用 ECR リポジトリにイメージをコピー。
これにより、イメージタグとライフサイクルを自分で管理可能。

### RETAIN ポリシー

ECR Repository と S3 Bucket はスタック削除時も保持（誤削除防止）。
