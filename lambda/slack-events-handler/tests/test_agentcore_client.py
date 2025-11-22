"""
Unit tests for AgentCore Runtime client.

This module tests the AgentCore client invocation logic,
including retry behavior for throttling exceptions.

Reference:
    AWS Bedrock AgentCore: https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html
"""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from agentcore_client import AgentCoreClient


def test_invoke_returns_result():
    """Test successful AgentCore invocation."""
    mock_client = Mock()
    mock_client.invoke_agent_runtime.return_value = {
        "contentType": "application/json",
        "response": [b'{"result": "Hello from agent"}'],
    }

    client = AgentCoreClient(
        "arn:aws:bedrock-agentcore:ap-northeast-1:123456789012:runtime/abc123"
    )
    client.client = mock_client

    result = client.invoke("test prompt")

    assert result["result"] == "Hello from agent"
    assert "sessionId" in result
    mock_client.invoke_agent_runtime.assert_called_once()


def test_session_id_generation():
    """Test session ID is at least 33 characters."""
    client = AgentCoreClient(
        "arn:aws:bedrock-agentcore:ap-northeast-1:123456789012:runtime/abc123"
    )
    session_id = client._generate_session_id()

    assert len(session_id) >= 33
    assert "-" in session_id  # Should contain hyphen separator


def test_throttling_retries_with_backoff():
    """Test throttling exception triggers exponential backoff."""
    mock_client = Mock()

    # Simulate throttling twice, then success
    mock_client.invoke_agent_runtime.side_effect = [
        ClientError({"Error": {"Code": "ThrottlingException"}}, "invoke_agent_runtime"),
        ClientError({"Error": {"Code": "ThrottlingException"}}, "invoke_agent_runtime"),
        {
            "contentType": "application/json",
            "response": [b'{"result": "Success after retry"}'],
        },
    ]

    client = AgentCoreClient(
        "arn:aws:bedrock-agentcore:ap-northeast-1:123456789012:runtime/abc123"
    )
    client.client = mock_client

    with patch("time.sleep"):  # Mock sleep to speed up test
        result = client.invoke("test prompt")

    assert result["result"] == "Success after retry"
    assert mock_client.invoke_agent_runtime.call_count == 3


def test_resource_not_found_raises_value_error():
    """Test ResourceNotFoundException raises ValueError."""
    mock_client = Mock()
    mock_client.invoke_agent_runtime.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException"}}, "invoke_agent_runtime"
    )

    client = AgentCoreClient(
        "arn:aws:bedrock-agentcore:ap-northeast-1:123456789012:runtime/abc123"
    )
    client.client = mock_client

    with pytest.raises(ValueError, match="AgentCore Runtime not found"):
        client.invoke("test prompt")


def test_max_retries_exceeded_raises_runtime_error():
    """Test max retries exceeded raises RuntimeError."""
    mock_client = Mock()
    mock_client.invoke_agent_runtime.side_effect = ClientError(
        {"Error": {"Code": "ThrottlingException"}}, "invoke_agent_runtime"
    )

    client = AgentCoreClient(
        "arn:aws:bedrock-agentcore:ap-northeast-1:123456789012:runtime/abc123"
    )
    client.client = mock_client

    with patch("time.sleep"):
        with pytest.raises(RuntimeError, match="AgentCore invocation failed"):
            client.invoke("test prompt", max_retries=3)


def test_custom_session_id():
    """Test custom session ID is used when provided."""
    mock_client = Mock()
    mock_client.invoke_agent_runtime.return_value = {
        "contentType": "application/json",
        "response": [b'{"result": "response"}'],
    }

    client = AgentCoreClient(
        "arn:aws:bedrock-agentcore:ap-northeast-1:123456789012:runtime/abc123"
    )
    client.client = mock_client

    custom_session_id = "custom-session-id-" + "a" * 20  # 33+ characters
    result = client.invoke("test prompt", session_id=custom_session_id)

    assert result["sessionId"] == custom_session_id
