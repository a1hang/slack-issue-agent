"""
AWS Bedrock AgentCore Runtime client.

This module provides a client for invoking AgentCore Runtime with automatic
session management and exponential backoff retry logic.

Reference:
    AWS Bedrock AgentCore: https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html
    AWS SDK Best Practices: Implement exponential backoff for throttling
"""

import json
import time
import uuid
from typing import Any

import boto3
from botocore.exceptions import ClientError


class AgentCoreClient:
    """
    Client for invoking AgentCore Runtime via boto3.

    This client handles session ID generation, payload formatting,
    and retry logic for throttling exceptions.

    Example:
        >>> client = AgentCoreClient(
        ...     agent_runtime_arn="arn:aws:bedrock-agentcore:ap-northeast-1:123456789012:runtime/abc123"
        ... )
        >>> result = client.invoke("Hello, how can I create a Trello issue?")
        >>> print(result['result'])
    """

    def __init__(self, agent_runtime_arn: str, region: str = "ap-northeast-1"):
        """
        Initialize AgentCore client.

        Args:
            agent_runtime_arn: ARN of AgentCore Runtime
                Format: arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:runtime/RUNTIME_ID
            region: AWS region name (default: ap-northeast-1)
        """
        self.client = boto3.client("bedrock-agentcore", region_name=region)
        self.agent_runtime_arn = agent_runtime_arn

    def _generate_session_id(self) -> str:
        """
        Generate a unique session ID for AgentCore.

        Returns:
            str: Session ID (73 characters, format: UUID-UUID)

        Note:
            AgentCore requires session IDs to be at least 33 characters long.
            We use two UUIDs concatenated with a hyphen to ensure uniqueness.
        """
        return f"{uuid.uuid4()}-{uuid.uuid4()}"

    def invoke(
        self, prompt: str, session_id: str | None = None, max_retries: int = 3
    ) -> dict[str, Any]:
        """
        Invoke AgentCore Runtime with user prompt.

        Args:
            prompt: User input message from Slack
            session_id: Optional session ID for conversation continuity
                Must be 33+ characters if provided
            max_retries: Maximum retry attempts for throttling (default: 3)

        Returns:
            dict: Agent response with keys:
                - result: str (agent's message)
                - sessionId: str (for conversation tracking)

        Raises:
            ValueError: AgentCore Runtime not found
            RuntimeError: AgentCore invocation failed after retries

        Security:
            - Requires IAM permission: bedrock-agentcore:InvokeAgentRuntime
            - Implements exponential backoff for ThrottlingException
        """
        if session_id is None:
            session_id = self._generate_session_id()

        payload = json.dumps({"prompt": prompt})
        retry_delay = 1  # Initial delay in seconds

        for attempt in range(max_retries):
            try:
                response = self.client.invoke_agent_runtime(
                    agentRuntimeArn=self.agent_runtime_arn,
                    runtimeSessionId=session_id,
                    payload=payload,
                    qualifier="DEFAULT",
                )

                # Parse response payload
                result = json.loads(response["payload"])
                return {"result": result.get("result", ""), "sessionId": session_id}

            except ClientError as e:
                error_code = e.response["Error"]["Code"]

                if error_code == "ThrottlingException" and attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    time.sleep(retry_delay * (2**attempt))
                    continue

                elif error_code == "ResourceNotFoundException":
                    raise ValueError(
                        f"AgentCore Runtime not found: {self.agent_runtime_arn}"
                    ) from e

                else:
                    raise RuntimeError(
                        f"AgentCore invocation failed: {error_code}"
                    ) from e

        # Max retries exceeded
        raise RuntimeError(
            f"AgentCore invocation failed after {max_retries} retries (throttling)"
        )
