import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";

export interface LambdaStackProps extends cdk.StackProps {
  agentRuntimeArn: string;
}

/**
 * LambdaStack - Lambda Function と Function URL
 *
 * このStackは以下のリソースを管理します:
 * - Lambda Function: Slack Events Handler (Python 3.12)
 * - Lambda Function URL: HTTPS エンドポイント (AUTH_TYPE: NONE)
 * - IAM Role: Lambda 実行用 (AgentCore, SSM, CloudWatch 権限)
 *
 * アーキテクチャ:
 * Slack Events API → Lambda Function URL → Lambda → AgentCore Runtime
 *
 * セキュリティ:
 * - Slack 署名検証による認証 (Function URL は AUTH_TYPE: NONE)
 * - SSM Parameter Store による機密情報管理
 * - 最小権限の IAM Policy (明示的 Resource ARN)
 * - DDoS 対策 (同時実行数制限)
 */
export class LambdaStack extends cdk.Stack {
  public readonly slackEventsHandler: lambda.Function;
  public readonly functionUrl: lambda.FunctionUrl;

  constructor(scope: Construct, id: string, props: LambdaStackProps) {
    super(scope, id, props);

    const { agentRuntimeArn } = props;

    // Lambda IAM Role
    // AWS Well-Architected Security Pillar: 最小権限の原則を適用
    // - AgentCore Runtime 呼び出し権限
    // - CloudWatch Logs 書き込み権限 (オブザーバビリティ)
    // - SSM Parameter Store 読み取り権限 (機密情報の安全な取得)
    // - KMS 復号化権限 (SSM SecureString 用、条件付き)
    const lambdaRole = new iam.Role(this, "LambdaRole", {
      // 信頼ポリシー: lambda サービスのみを許可
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      description: "Execution role for Slack Events Handler Lambda",
      managedPolicies: [
        // CloudWatch Logs 基本権限 (AWS管理ポリシー)
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSLambdaBasicExecutionRole",
        ),
      ],
    });

    // AgentCore Runtime 呼び出し権限
    // Slack イベントを AgentCore に転送するために必要
    lambdaRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["bedrock-agentcore:InvokeAgentRuntime"],
        // AgentCore Runtime と runtime-endpoint へのアクセスを許可
        resources: [agentRuntimeArn, `${agentRuntimeArn}/*`],
      }),
    );

    // SSM Parameter Store 読み取り権限
    // Slack 署名検証用シークレット (signing-secret) を安全に取得
    // パラメータパスを限定して最小権限を実現
    lambdaRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ssm:GetParameter", "ssm:GetParameters"],
        resources: [
          `arn:aws:ssm:${this.region}:${this.account}:parameter/slack-issue-agent/*`,
        ],
      }),
    );

    // KMS 復号化権限 (SSM SecureString 用)
    // SSM SecureString パラメータの復号化に必要
    // kms:ViaService 条件で SSM 経由のみに制限し、直接的な KMS アクセスを防止
    lambdaRole.addToPolicy(
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

    // CloudWatch Logs Group
    // AWS Well-Architected Operational Excellence Pillar: ログの長期保存
    // コンプライアンス・監査・トラブルシューティングのため、90日保持
    const logGroup = new logs.LogGroup(this, "SlackEventsHandlerLogGroup", {
      logGroupName: "/aws/lambda/SlackIssueAgent-SlackEventsHandler",
      retention: logs.RetentionDays.THREE_MONTHS,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Lambda Function
    // Slack Events API からのリクエストを受け取り、AgentCore Runtime に転送
    this.slackEventsHandler = new lambda.Function(this, "SlackEventsHandler", {
      // Python 3.12 ランタイム (AWS推奨の最新安定版)
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "handler.lambda_handler",
      // ソースコードと依存関係を含むアセット
      // 依存関係は lib/python/ に事前インストール済み
      // exclude で不要なファイル (テスト、仮想環境) を除外
      code: lambda.Code.fromAsset("../lambda/slack-events-handler", {
        exclude: [
          "tests",
          ".venv",
          "__pycache__",
          "*.pyc",
          ".pytest_cache",
          "requirements-dev.txt",
        ],
      }),
      role: lambdaRole,

      // Timeout: 90秒 (AgentCore 処理完了を待機)
      // 注: Slack Events API は 3秒以内に HTTP 200 応答を期待するが、
      //     現在は同期処理のため AgentCore のレスポンスを待つ必要がある
      //     将来的には AgentCore Gateway 経由で非同期化を検討
      timeout: cdk.Duration.seconds(90),

      // Memory: 512MB (Slack 署名検証とイベント転送に十分)
      memorySize: 512,

      // DDoS 対策: 同時実行数制限
      // Slack からの大量リクエストに対する保護
      reservedConcurrentExecutions: 10,

      description: "Slack Events API handler with AgentCore integration",

      // Environment Variables
      // AWS Well-Architected Security Pillar: 環境変数に機密情報を含めない
      // 機密情報 (Slack signing-secret) は SSM Parameter Store から実行時に取得
      environment: {
        AGENTCORE_RUNTIME_ARN: agentRuntimeArn,
        LOG_LEVEL: "INFO",
        // AWS_REGION は Lambda runtime で自動的に設定される
      },

      // CloudWatch Logs Group (logRetention は非推奨)
      logGroup: logGroup,
    });

    // Lambda Function URL
    // Slack Events API からの HTTPS リクエストを受け付けるエンドポイント
    //
    // セキュリティ:
    // - AUTH_TYPE: NONE (Slack 署名検証をアプリケーションレイヤーで実施)
    // - HTTPS のみサポート (TLS 1.2+)
    // - IPv4 と IPv6 の両方をサポート (Lambda Function URL のデフォルト動作)
    this.functionUrl = this.slackEventsHandler.addFunctionUrl({
      // 認証タイプ: NONE
      // Slack 署名検証は Lambda 関数内で実装 (x-slack-signature, x-slack-request-timestamp)
      authType: lambda.FunctionUrlAuthType.NONE,

      // CORS 設定
      cors: {
        // Slack Events API からのリクエストを許可
        // Slack は動的 IP を使用するため、Origin での制限は困難
        allowedOrigins: ["*"],

        // POST メソッドのみ許可 (Slack Events API 仕様)
        allowedMethods: [lambda.HttpMethod.POST],

        // Slack 署名検証に必要なヘッダーを許可
        allowedHeaders: [
          "Content-Type",
          "x-slack-signature",
          "x-slack-request-timestamp",
        ],
      },
    });

    // CloudFormation Outputs
    // デプロイ後の確認と Slack App 設定用
    new cdk.CfnOutput(this, "FunctionUrl", {
      value: this.functionUrl.url,
      description:
        "Lambda Function URL for Slack Events API (register this in Slack App settings)",
    });

    new cdk.CfnOutput(this, "LambdaFunctionArn", {
      value: this.slackEventsHandler.functionArn,
      exportName: `${cdk.Stack.of(this).stackName}-LambdaFunctionArn`,
      description: "Lambda Function ARN for Slack Events Handler",
    });

    new cdk.CfnOutput(this, "LambdaRoleArn", {
      value: lambdaRole.roleArn,
      description: "IAM Role ARN for Lambda Execution",
    });
  }
}
