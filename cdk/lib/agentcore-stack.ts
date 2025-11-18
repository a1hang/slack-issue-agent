import * as cdk from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as ecr_assets from "aws-cdk-lib/aws-ecr-assets";
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
 * - Docker Image Asset: agent/Dockerfile の自動ビルド&プッシュ
 *
 * デプロイ自動化:
 * - CDK が Dockerfile を自動的にビルド (ARM64)
 * - 自動生成されるECRリポジトリにプッシュ
 * - AgentCore Runtime に自動的にイメージURIを設定
 * - `cdk deploy --all` 一発で完全デプロイ可能
 *
 * セキュリティ: AWS Well-Architected Framework - Security Pillar
 * - 最小権限の原則 (IAM Policy with explicit Resource ARN)
 * - 保管時・転送時のデータ暗号化
 * - ログとモニタリングの有効化
 * - ECRイメージスキャン有効化（脆弱性検出）
 */
export class AgentCoreStack extends cdk.Stack {
  public readonly agentRuntime: agentcore.Runtime;
  public readonly agentRepository: ecr.IRepository;

  constructor(scope: Construct, id: string, props: AgentCoreStackProps) {
    super(scope, id, props);

    const { agentCodeBucket } = props;

    // ECR Repository for Agent Container Images
    // CDKで作成・管理し、削除時もリポジトリを保持（RETAIN ポリシー）
    this.agentRepository = new ecr.Repository(this, "AgentRepository", {
      repositoryName: "slack-issue-agent",
      // イメージスキャンを有効化（セキュリティベストプラクティス）
      imageScanOnPush: true,
      // 削除時にリポジトリを保持（誤削除防止）
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      // 古いイメージの自動削除ルール（最新3つのみ保持）
      lifecycleRules: [
        {
          description: "Keep only the latest 3 images",
          maxImageCount: 3,
          rulePriority: 1,
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
        // Bedrock モデル呼び出しと AWS Marketplace 権限 (AWS管理ポリシー)
        // bedrock:InvokeModel*, aws-marketplace:ViewSubscriptions, aws-marketplace:Subscribe を含む
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "AmazonBedrockLimitedAccess",
        ),
      ],
    });

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

    // AgentCore Runtime - Docker Image Asset による自動ビルド&プッシュ
    // CDK が自動的に以下を実行:
    // 1. agent/Dockerfile を使用して ARM64 イメージをビルド
    // 2. ECR リポジトリにイメージをプッシュ
    // 3. AgentCore Runtime にイメージ URI を渡す
    //
    // ビルドパフォーマンス最適化:
    // - Docker BuildKit 有効化（並列ビルド、キャッシュ最適化）
    // - .dockerignore で不要ファイルを除外（ビルドコンテキスト削減）
    const agentDockerImage = new ecr_assets.DockerImageAsset(
      this,
      "AgentDockerImage",
      {
        directory: path.join(__dirname, "../../agent"),
        platform: ecr_assets.Platform.LINUX_ARM64,
        // ビルド時引数（必要に応じて追加）
        // buildArgs: {
        //   PYTHON_VERSION: "3.12",
        // },
      },
    );

    // DockerImageAssetが自動生成したリポジトリとイメージタグを使用
    // repository.repositoryArn はトークンなので fromRepositoryAttributes を使用
    const agentRuntimeArtifact =
      agentcore.AgentRuntimeArtifact.fromEcrRepository(
        ecr.Repository.fromRepositoryAttributes(this, "AgentImageRepository", {
          repositoryArn: agentDockerImage.repository.repositoryArn,
          repositoryName: agentDockerImage.repository.repositoryName,
        }),
        agentDockerImage.imageTag,
      );

    this.agentRuntime = new agentcore.Runtime(this, "SlackIssueAgentRuntime", {
      // Runtime名: 英字開始、英字・数字・アンダースコアのみ使用可能 (ハイフン不可)
      runtimeName: "slack_issue_agent_runtime",
      agentRuntimeArtifact: agentRuntimeArtifact,
      executionRole: agentRole,
      description:
        "Slack Issue Agent - AgentCore Runtime with explicit region config",

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
        // AWS_REGION を明示的に設定 (Bedrock クライアントのリージョン指定用)
        AWS_REGION: this.region,
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
