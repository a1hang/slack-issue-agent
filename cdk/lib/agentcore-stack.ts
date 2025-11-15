import * as cdk from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as agentcore from "@aws-cdk/aws-bedrock-agentcore-alpha";
import { Construct } from "constructs";
import * as path from "path";

export interface AgentCoreStackProps extends cdk.StackProps {
  agentCodeBucket: s3.IBucket;
}

/**
 * AgentCoreStack - AgentCore Runtime と IAM Role
 *
 * このStackは以下のリソースを管理します:
 * - AgentCore Runtime: Strands Agent の実行環境 (コンテナベース)
 * - IAM Role: AgentCore 実行用 (Bedrock, SSM, CloudWatch 権限)
 * - ECR Repository: Agent コンテナイメージ保存
 *
 * デプロイ方式: ECR + Docker コンテナベース
 * - AWS CDK AgentCore alpha版 (v2.224.0+) はコンテナデプロイのみサポート
 * - 将来的な Direct Code Deployment (Zip) サポートについては GitHub Issue #8 を参照
 *
 * セキュリティ: AWS Well-Architected Framework - Security Pillar
 * - 最小権限の原則 (IAM Policy with explicit Resource ARN)
 * - 保管時・転送時のデータ暗号化
 * - ログとモニタリングの有効化
 */
export class AgentCoreStack extends cdk.Stack {
  public readonly agentRuntime: agentcore.Runtime;
  public readonly agentRepository: ecr.Repository;

  constructor(scope: Construct, id: string, props: AgentCoreStackProps) {
    super(scope, id, props);

    const { agentCodeBucket } = props;

    // ECR Repository for Agent Container Images
    // Agent のDockerイメージを保存
    this.agentRepository = new ecr.Repository(this, "AgentRepository", {
      repositoryName: "slack-issue-agent",
      // イメージスキャン有効化 (セキュリティベストプラクティス)
      imageScanOnPush: true,
      // Removal Policy: RETAIN (誤削除防止)
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      // 古いイメージの自動削除ルール (最新10個を保持)
      lifecycleRules: [
        {
          description: "Keep last 10 images",
          maxImageCount: 10,
        },
      ],
    });

    // AgentCore IAM Role
    // AWS Well-Architected Security Pillar: 最小権限の原則を適用
    // - Bedrock Claude モデル呼び出し権限
    // - CloudWatch Logs 書き込み権限 (オブザーバビリティ)
    // - SSM Parameter Store 読み取り権限 (機密情報の安全な取得)
    // - KMS 復号化権限 (SSM SecureString 用、条件付き)
    const agentRole = new iam.Role(this, "AgentCoreRole", {
      // 信頼ポリシー: bedrock-agentcore サービスのみを許可
      assumedBy: new iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
      description: "Execution role for Slack Issue Agent on AgentCore Runtime",
      managedPolicies: [
        // CloudWatch Logs 基本権限 (AWS管理ポリシー)
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSLambdaBasicExecutionRole",
        ),
      ],
    });

    // Bedrock Model 呼び出し権限
    // Amazon Bedrock Claude モデルへのアクセスを許可
    // Sonnet 4.5 を使用想定だが、Claude モデルファミリー全体を許可
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        // 明示的な Resource ARN 指定 (最小権限の原則)
        resources: [
          `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-*`,
        ],
      }),
    );

    // SSM Parameter Store 読み取り権限
    // 機密情報 (Slack Bot Token, Trello API Key/Token) を安全に取得
    // パラメータパスを限定して最小権限を実現
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ssm:GetParameter", "ssm:GetParameters"],
        resources: [
          `arn:aws:ssm:${this.region}:${this.account}:parameter/slack-issue-agent/slack/bot-token`,
          `arn:aws:ssm:${this.region}:${this.account}:parameter/slack-issue-agent/trello/*`,
        ],
      }),
    );

    // KMS 復号化権限 (SSM SecureString 用)
    // SSM SecureString パラメータの復号化に必要
    // kms:ViaService 条件で SSM 経由のみに制限し、直接的な KMS アクセスを防止
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["kms:Decrypt"],
        resources: [`arn:aws:kms:${this.region}:${this.account}:key/*`],
        conditions: {
          StringEquals: {
            "kms:ViaService": `ssm.${this.region}.amazonaws.com`,
          },
        },
      }),
    );

    // X-Ray トレーシング権限 (オプション、デバッグ用)
    // AWS X-Ray による分散トレーシングを有効化
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
        // X-Ray API は resource ARN をサポートしないため、'*' を使用
        resources: ["*"],
      }),
    );

    // AgentCore Runtime
    // AWS Bedrock AgentCore でのコンテナベースデプロイメント
    //
    // デプロイ前提条件:
    // 1. agent/ ディレクトリに Dockerfile が存在すること
    // 2. ECR に ARM64 イメージを事前にプッシュすること
    //
    // ビルド・プッシュ手順:
    // ```bash
    // docker buildx build --platform linux/arm64 -t slack-issue-agent:latest .
    // docker tag slack-issue-agent:latest <account>.dkr.ecr.<region>.amazonaws.com/slack-issue-agent:latest
    // aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
    // docker push <account>.dkr.ecr.<region>.amazonaws.com/slack-issue-agent:latest
    // ```
    const agentRuntimeArtifact =
      agentcore.AgentRuntimeArtifact.fromEcrRepository(
        this.agentRepository,
        "latest", // イメージタグ
      );

    this.agentRuntime = new agentcore.Runtime(this, "SlackIssueAgentRuntime", {
      // Runtime名: 英字開始、英字・数字・アンダースコアのみ使用可能 (ハイフン不可)
      runtimeName: "slack_issue_agent_runtime",
      agentRuntimeArtifact: agentRuntimeArtifact,
      executionRole: agentRole,
      description: "Slack Issue Agent - Bedrock AgentCore Runtime",

      // Network Configuration: Public Network Mode (VPC 不使用)
      // AgentCore が外部 API (Slack, Trello) にアクセスするため、Public Network を使用
      networkConfiguration:
        agentcore.RuntimeNetworkConfiguration.usingPublicNetwork(),

      // Protocol Configuration: HTTP (AgentCore デフォルト)
      protocolConfiguration: agentcore.ProtocolType.HTTP,

      // Environment Variables
      // AWS Well-Architected Security Pillar: 環境変数に機密情報を含めない
      // 機密情報は SSM Parameter Store から実行時に取得
      environmentVariables: {
        LOG_LEVEL: "INFO",
        // AWS_REGION は AgentCore runtime で自動的に利用可能
      },
    });

    // CloudFormation Outputs
    // Lambda Function による AgentCore 呼び出しと、デプロイ後の確認に使用
    new cdk.CfnOutput(this, "AgentCoreRuntimeArn", {
      value: this.agentRuntime.agentRuntimeArn,
      exportName: `${cdk.Stack.of(this).stackName}-AgentCoreRuntimeArn`,
      description: "AgentCore Runtime ARN for Lambda invocation",
    });

    new cdk.CfnOutput(this, "AgentCoreRuntimeId", {
      value: this.agentRuntime.agentRuntimeId,
      exportName: `${cdk.Stack.of(this).stackName}-AgentCoreRuntimeId`,
      description: "AgentCore Runtime ID",
    });

    new cdk.CfnOutput(this, "AgentRepositoryUri", {
      value: this.agentRepository.repositoryUri,
      description: "ECR Repository URI for Agent container images",
    });

    // CloudWatch Logs 保持期間設定
    // AWS Well-Architected Operational Excellence Pillar: ログの長期保存
    // コンプライアンス・監査・トラブルシューティングのため、90日以上の保持を推奨
    // Note: CDK alpha版では直接設定できない可能性があるため、
    // Custom Resource で設定するか、デプロイ後に AWS Console/CLI で設定
  }
}
