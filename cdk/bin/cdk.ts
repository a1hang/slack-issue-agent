#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { SharedStack } from "../lib/shared-stack";
import { AgentCoreStack } from "../lib/agentcore-stack";
import { LambdaStack } from "../lib/lambda-stack";

/**
 * Slack Issue Agent - CDK Application
 *
 * このアプリケーションは以下の3つのStackで構成されます:
 * 1. SharedStack: S3 Bucket (Agent コードデプロイ用)
 * 2. AgentCoreStack: AgentCore Runtime + IAM Role + ECR Repository
 * 3. LambdaStack: Lambda Function + Function URL + IAM Role
 *
 * Stack 依存関係:
 * LambdaStack → AgentCoreStack → SharedStack
 *
 * デプロイ順序:
 * cdk deploy SlackIssueAgentSharedStack
 * cdk deploy SlackIssueAgentAgentCoreStack
 * cdk deploy SlackIssueAgentLambdaStack
 *
 * または一括デプロイ:
 * cdk deploy --all
 */

const app = new cdk.App();

// AWS アカウント・リージョン設定
// CDK デプロイ環境を環境変数から取得
// デフォルトリージョン: ap-northeast-1 (東京)
const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID,
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
