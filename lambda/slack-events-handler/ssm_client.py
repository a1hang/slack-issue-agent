"""
AWS SSM Parameter Store client with caching.

This module provides a client for retrieving SecureString parameters from
AWS Systems Manager Parameter Store with automatic KMS decryption and LRU caching.

Reference:
    AWS SSM Parameter Store: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html
    IAM Best Practices: Use least-privilege access policies
"""

import boto3
from functools import lru_cache


class SSMParameterStore:
    """
    Client for retrieving SSM parameters with caching.

    This client uses LRU cache to avoid redundant SSM API calls within the same
    Lambda execution context. The cache is automatically cleared between Lambda
    invocations.

    Example:
        >>> ssm = SSMParameterStore()
        >>> slack_token = ssm.get_parameter('/slack-issue-agent/slack/bot-token')
        >>> signing_secret = ssm.get_parameter('/slack-issue-agent/slack/signing-secret')
    """

    def __init__(self, region: str = "ap-northeast-1"):
        """
        Initialize SSM Parameter Store client.

        Args:
            region: AWS region name (default: ap-northeast-1)
        """
        self.client = boto3.client("ssm", region_name=region)

    @lru_cache(maxsize=128)
    def get_parameter(self, name: str, with_decryption: bool = True) -> str:
        """
        Retrieve SSM parameter value with caching.

        Args:
            name: Parameter name (e.g., /slack-issue-agent/slack/bot-token)
            with_decryption: Auto-decrypt SecureString (default: True)

        Returns:
            str: Parameter value (decrypted if SecureString)

        Raises:
            ClientError: Parameter does not exist or access denied

        Note:
            Uses @lru_cache to avoid redundant SSM API calls within Lambda execution.
            The cache persists only during the current Lambda execution context.

        Security:
            - Requires IAM permission: ssm:GetParameter
            - Requires IAM permission: kms:Decrypt (for SecureString)
            - KMS decryption is restricted to SSM service via IAM Condition
        """
        response = self.client.get_parameter(Name=name, WithDecryption=with_decryption)
        return response["Parameter"]["Value"]
