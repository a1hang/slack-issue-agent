import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as ssm from "aws-cdk-lib/aws-ssm";
import { Construct } from "constructs";

/**
 * SharedStack - 共有リソース (S3 Bucket, SSM Parameter 検証)
 *
 * このStackは以下のリソースを管理します:
 * - S3 Bucket: Agent デプロイパッケージを保存
 * - SSM Parameter 検証: 必要なパラメータの存在確認
 *
 * AWS Well-Architected Framework - Security Pillar に基づき、
 * データ保護とアクセス管理のベストプラクティスを適用しています。
 */
export class SharedStack extends cdk.Stack {
  public readonly agentCodeBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 Bucket for Agent Code Deployment Package
    // AWS Well-Architected Security Pillar: データ保護のベストプラクティス
    // - 保管時の暗号化 (SSE-S3)
    // - 転送時の暗号化 (SSL/TLS)
    // - パブリックアクセスのブロック
    this.agentCodeBucket = new s3.Bucket(this, "AgentCodeBucket", {
      // S3 Managed 暗号化 (SSE-S3) - AWS推奨のデフォルト暗号化
      encryption: s3.BucketEncryption.S3_MANAGED,

      // SSL/TLS 強制 - セキュアな転送の必須化
      enforceSSL: true,

      // バージョニング有効化 - デプロイパッケージの履歴管理と復旧可能性
      versioned: true,

      // Removal Policy: RETAIN - 誤削除防止 (Stateful リソース)
      removalPolicy: cdk.RemovalPolicy.RETAIN,

      // Public Access Block - すべてのパブリックアクセスをブロック
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,

      // Object Ownership - ACL 無効化 (Bucket Policy による集中管理)
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
    });

    // SSM Parameter Store 検証
    // デプロイ前に必要なパラメータの存在を検証することで、
    // ランタイムエラーを防ぎ、デプロイの信頼性を向上させます。
    // パラメータが存在しない場合、CDK デプロイは失敗します。
    const requiredParameters = [
      "/slack-issue-agent/slack/bot-token",
      "/slack-issue-agent/slack/signing-secret",
      "/slack-issue-agent/trello/api-key",
      "/slack-issue-agent/trello/token",
    ];

    // 各パラメータの存在確認 (既存パラメータを参照)
    // SecureString 形式で KMS 暗号化された値を想定
    requiredParameters.forEach((paramName) => {
      const param = ssm.StringParameter.fromSecureStringParameterAttributes(
        this,
        `Param${paramName.replace(/\//g, "")}`,
        {
          parameterName: paramName,
          // version は指定しない (最新を常に参照)
        },
      );

      // パラメータARNをCfnOutputとして出力 (デバッグ・監査用)
      new cdk.CfnOutput(this, `SSMParameter${paramName.replace(/\//g, "")}`, {
        value: param.parameterArn,
        description: `SSM Parameter ARN for ${paramName}`,
      });
    });

    // CloudFormation Outputs
    // デプロイ後の確認と他スタックからの参照用
    new cdk.CfnOutput(this, "AgentCodeBucketName", {
      value: this.agentCodeBucket.bucketName,
      exportName: `${cdk.Stack.of(this).stackName}-AgentCodeBucketName`,
      description: "S3 Bucket name for Agent deployment package",
    });

    new cdk.CfnOutput(this, "AgentCodeBucketArn", {
      value: this.agentCodeBucket.bucketArn,
      exportName: `${cdk.Stack.of(this).stackName}-AgentCodeBucketArn`,
      description: "S3 Bucket ARN for Agent deployment package",
    });
  }
}
