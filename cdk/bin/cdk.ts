#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { SharedStack } from "../lib/shared-stack";
import { AgentCoreStack } from "../lib/agentcore-stack";
import { LambdaStack } from "../lib/lambda-stack";

console.log("[DEBUG] CDK app starting...");

/**
 * Slack Issue Agent - CDK Application
 *
 * このアプリケーションは以下の3つのStackで構成されます:
 * 1. SharedStack: S3 Bucket (Agent コードデプロイ用)
 * 2. AgentCoreStack: AgentCore Runtime + IAM Role + ECR Repository + Docker Image Asset
 * 3. LambdaStack: Lambda Function + Function URL + IAM Role
 *
 * Stack 依存関係:
 * LambdaStack → AgentCoreStack → SharedStack
 *
 * デプロイ自動化:
 * - CDKが自動的にDockerイメージをビルド&プッシュ
 * - SSM Parameter Storeの事前設定のみ必要
 * - `cdk deploy --all` 一発で完全デプロイ
 *
 * デプロイ前提条件:
 * 1. SSM Parameter Store設定 (DEPLOYMENT_GUIDE.md 参照)
 * 2. Docker デーモンが起動していること
 * 3. AWS CLI認証設定完了
 */

const app = new cdk.App();

// AWS アカウント・リージョン設定
// CDK デプロイ環境を環境変数から取得
// デフォルトリージョン: ap-northeast-1 (東京)
// account が未設定の場合は undefined にして CDK に自動検出させる
const env = {
  account:
    process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID || undefined,
  region:
    process.env.CDK_DEFAULT_REGION ||
    process.env.AWS_REGION ||
    "ap-northeast-1",
};

// 1. SharedStack - 共有リソース (S3 Bucket)
const sharedStack = new SharedStack(app, "SlackIssueAgentSharedStack", {
  env,
  description:
    "Shared resources for Slack Issue Agent (S3 Bucket, SSM Parameter validation)",
});

// 2. AgentCoreStack - AgentCore Runtime
const agentCoreStack = new AgentCoreStack(
  app,
  "SlackIssueAgentAgentCoreStack",
  {
    agentCodeBucket: sharedStack.agentCodeBucket,
    env,
    description:
      "AgentCore Runtime for Slack Issue Agent (Strands Agent on Bedrock)",
  },
);

// 3. LambdaStack - Lambda Function + Function URL
const lambdaStack = new LambdaStack(app, "SlackIssueAgentLambdaStack", {
  agentRuntimeArn: agentCoreStack.agentRuntime.agentRuntimeArn,
  env,
  description: "Lambda Function for Slack Events API integration",
});

// Stack 依存関係の明示的な定義
// CDK デプロイ順序を制御し、依存関係を明確化
// LambdaStack → AgentCoreStack → SharedStack
//
// 削除時の注意:
// - Stateful リソース (S3, ECR) は RemovalPolicy.RETAIN により保護
// - Stack 削除時も実際のリソースは残る (誤削除防止)
agentCoreStack.addDependency(sharedStack);
lambdaStack.addDependency(agentCoreStack);
