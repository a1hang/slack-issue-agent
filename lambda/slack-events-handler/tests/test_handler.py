"""
Unit tests for Lambda handler.

This module tests the main Lambda handler logic including
signature verification, URL verification, and error handling.

Reference:
    Slack Events API: https://api.slack.com/apis/connections/events-api
"""

import hashlib
import hmac
import time
from unittest.mock import Mock, patch


from handler import lambda_handler, mask_sensitive_data


def test_missing_signature_returns_400():
    """Test that missing x-slack-signature returns 400."""
    event = {"headers": {"x-slack-request-timestamp": "1234567890"}, "body": "{}"}

    response = lambda_handler(event, Mock())

    assert response["statusCode"] == 400
    assert "Missing required headers" in response["body"]


def test_missing_timestamp_returns_400():
    """Test that missing x-slack-request-timestamp returns 400."""
    event = {"headers": {"x-slack-signature": "v0=abc"}, "body": "{}"}

    response = lambda_handler(event, Mock())

    assert response["statusCode"] == 400
    assert "Missing required headers" in response["body"]


def test_invalid_signature_returns_401():
    """Test that invalid signature returns 401."""
    event = {
        "headers": {
            "x-slack-signature": "v0=invalid",
            "x-slack-request-timestamp": str(int(time.time())),
        },
        "body": '{"type":"event_callback"}',
    }

    with patch("handler.SSMParameterStore.get_parameter", return_value="secret"):
        response = lambda_handler(event, Mock())

    assert response["statusCode"] == 401
    assert "Invalid signature" in response["body"]


def test_url_verification_returns_challenge():
    """Test URL verification flow."""
    timestamp = str(int(time.time()))
    body = '{"type":"url_verification","challenge":"test_challenge"}'
    signing_secret = "test_secret"

    # Generate valid signature
    basestring = f"v0:{timestamp}:{body}".encode("utf-8")
    signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"), basestring, hashlib.sha256
        ).hexdigest()
    )

    event = {
        "headers": {
            "x-slack-signature": signature,
            "x-slack-request-timestamp": timestamp,
        },
        "body": body,
    }

    with patch("handler.SSMParameterStore.get_parameter", return_value=signing_secret):
        response = lambda_handler(event, Mock())

    assert response["statusCode"] == 200
    assert "test_challenge" in response["body"]


def test_successful_event_callback():
    """Test successful event callback processing."""
    timestamp = str(int(time.time()))
    body = '{"type":"event_callback","event":{"text":"Hello agent"}}'
    signing_secret = "test_secret"

    # Generate valid signature
    basestring = f"v0:{timestamp}:{body}".encode("utf-8")
    signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"), basestring, hashlib.sha256
        ).hexdigest()
    )

    event = {
        "headers": {
            "x-slack-signature": signature,
            "x-slack-request-timestamp": timestamp,
        },
        "body": body,
    }

    mock_agentcore_client = Mock()
    mock_agentcore_client.invoke.return_value = {
        "result": "Agent response",
        "sessionId": "test-session-id",
    }

    with patch("handler.SSMParameterStore.get_parameter", return_value=signing_secret):
        with patch("handler.AgentCoreClient", return_value=mock_agentcore_client):
            with patch.dict("os.environ", {"AGENTCORE_RUNTIME_ARN": "arn:test"}):
                response = lambda_handler(event, Mock())

    assert response["statusCode"] == 200
    assert "ok" in response["body"]
    mock_agentcore_client.invoke.assert_called_once_with(prompt="Hello agent")


def test_base64_encoded_body():
    """Test Base64 encoded body is decoded correctly."""
    import base64

    timestamp = str(int(time.time()))
    body = '{"type":"url_verification","challenge":"test"}'
    encoded_body = base64.b64encode(body.encode("utf-8")).decode("utf-8")
    signing_secret = "test_secret"

    # Generate signature from decoded body
    basestring = f"v0:{timestamp}:{body}".encode("utf-8")
    signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"), basestring, hashlib.sha256
        ).hexdigest()
    )

    event = {
        "headers": {
            "x-slack-signature": signature,
            "x-slack-request-timestamp": timestamp,
        },
        "body": encoded_body,
        "isBase64Encoded": True,
    }

    with patch("handler.SSMParameterStore.get_parameter", return_value=signing_secret):
        response = lambda_handler(event, Mock())

    assert response["statusCode"] == 200


def test_invalid_json_returns_400():
    """Test invalid JSON payload returns 400."""
    timestamp = str(int(time.time()))
    body = "{invalid json"
    signing_secret = "test_secret"

    # Generate valid signature (even though JSON is invalid)
    basestring = f"v0:{timestamp}:{body}".encode("utf-8")
    signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"), basestring, hashlib.sha256
        ).hexdigest()
    )

    event = {
        "headers": {
            "x-slack-signature": signature,
            "x-slack-request-timestamp": timestamp,
        },
        "body": body,
    }

    with patch("handler.SSMParameterStore.get_parameter", return_value=signing_secret):
        response = lambda_handler(event, Mock())

    assert response["statusCode"] == 400
    assert "Invalid JSON payload" in response["body"]


def test_mask_sensitive_data():
    """Test sensitive data masking."""
    text = "Token: xoxb-123456789-abcdef Signature: v0=abcdef0123456789"
    masked = mask_sensitive_data(text)

    assert "xoxb-123456789-abcdef" not in masked
    assert "xoxb-***MASKED***" in masked
    assert "v0=abcdef0123456789" not in masked or "v0=***MASKED***" in masked
