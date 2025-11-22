"""
Integration tests for Lambda Function URL.

These tests verify the deployed Lambda function works correctly with
actual HTTP requests to the Function URL. They require:
- Deployed Lambda Function URL
- Valid Slack signing secret in SSM

Environment Variables:
    FUNCTION_URL: Lambda Function URL (required)
    SLACK_SIGNING_SECRET: Slack signing secret for test requests (required)

Reference:
    Slack Events API: https://api.slack.com/apis/connections/events-api
"""

import hashlib
import hmac
import json
import os
import time

import pytest
import requests


# Skip all tests if environment variables are not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("FUNCTION_URL") or not os.environ.get("SLACK_SIGNING_SECRET"),
    reason="Integration test environment variables not set (FUNCTION_URL, SLACK_SIGNING_SECRET)",
)


def generate_slack_signature(body: str, timestamp: str, signing_secret: str) -> str:
    """
    Generate valid Slack signature for testing.

    Args:
        body: Request body as string
        timestamp: Unix timestamp as string
        signing_secret: Slack signing secret

    Returns:
        str: Slack signature in format "v0=<hash>"
    """
    basestring = f"v0:{timestamp}:{body}".encode("utf-8")
    signature = hmac.new(
        signing_secret.encode("utf-8"), basestring, hashlib.sha256
    ).hexdigest()
    return f"v0={signature}"


@pytest.fixture
def function_url():
    """Get Function URL from environment."""
    return os.environ["FUNCTION_URL"]


@pytest.fixture
def signing_secret():
    """Get Slack signing secret from environment."""
    return os.environ["SLACK_SIGNING_SECRET"]


class TestURLVerification:
    """Tests for Slack URL verification flow."""

    def test_url_verification_returns_challenge(self, function_url, signing_secret):
        """
        Test URL verification event returns challenge.

        Slack sends this during app setup to verify the endpoint.
        """
        timestamp = str(int(time.time()))
        body = json.dumps(
            {
                "type": "url_verification",
                "challenge": "test_challenge_12345",
            }
        )

        signature = generate_slack_signature(body, timestamp, signing_secret)

        response = requests.post(
            function_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-slack-signature": signature,
                "x-slack-request-timestamp": timestamp,
            },
            timeout=30,
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("challenge") == "test_challenge_12345"


class TestSignatureVerification:
    """Tests for Slack signature verification."""

    def test_invalid_signature_returns_401(self, function_url):
        """
        Test invalid signature returns HTTP 401.

        Security: Ensures unauthorized requests are rejected.
        """
        timestamp = str(int(time.time()))
        body = json.dumps({"type": "event_callback"})

        response = requests.post(
            function_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-slack-signature": "v0=invalid_signature",
                "x-slack-request-timestamp": timestamp,
            },
            timeout=30,
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_missing_signature_returns_400(self, function_url):
        """
        Test missing signature header returns HTTP 400.

        Security: Ensures requests without signatures are rejected.
        """
        timestamp = str(int(time.time()))
        body = json.dumps({"type": "event_callback"})

        response = requests.post(
            function_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-slack-request-timestamp": timestamp,
            },
            timeout=30,
        )

        assert response.status_code == 400

    def test_missing_timestamp_returns_400(self, function_url):
        """
        Test missing timestamp header returns HTTP 400.
        """
        body = json.dumps({"type": "event_callback"})

        response = requests.post(
            function_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-slack-signature": "v0=test",
            },
            timeout=30,
        )

        assert response.status_code == 400

    def test_expired_timestamp_returns_401(self, function_url, signing_secret):
        """
        Test expired timestamp (>5 min old) returns HTTP 401.

        Security: Prevents replay attacks.
        """
        # Timestamp from 10 minutes ago
        timestamp = str(int(time.time()) - 600)
        body = json.dumps({"type": "event_callback"})

        signature = generate_slack_signature(body, timestamp, signing_secret)

        response = requests.post(
            function_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-slack-signature": signature,
                "x-slack-request-timestamp": timestamp,
            },
            timeout=30,
        )

        assert response.status_code == 401


class TestPayloadValidation:
    """Tests for request payload validation."""

    def test_invalid_json_returns_400(self, function_url, signing_secret):
        """
        Test invalid JSON payload returns HTTP 400.
        """
        timestamp = str(int(time.time()))
        body = "{invalid json"

        signature = generate_slack_signature(body, timestamp, signing_secret)

        response = requests.post(
            function_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-slack-signature": signature,
                "x-slack-request-timestamp": timestamp,
            },
            timeout=30,
        )

        assert response.status_code == 400

    def test_missing_event_key_returns_400(self, function_url, signing_secret):
        """
        Test event_callback without 'event' key returns HTTP 400.
        """
        timestamp = str(int(time.time()))
        body = json.dumps({"type": "event_callback"})

        signature = generate_slack_signature(body, timestamp, signing_secret)

        response = requests.post(
            function_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-slack-signature": signature,
                "x-slack-request-timestamp": timestamp,
            },
            timeout=30,
        )

        assert response.status_code == 400


class TestBotMessageFiltering:
    """Tests for bot message filtering to prevent loops."""

    def test_bot_message_returns_200_ok(self, function_url, signing_secret):
        """
        Test bot messages are ignored (returns 200 without processing).

        Security: Prevents infinite loops when bot responds to itself.
        """
        timestamp = str(int(time.time()))
        body = json.dumps(
            {
                "type": "event_callback",
                "event": {
                    "type": "message",
                    "text": "Bot message",
                    "bot_id": "B12345",
                    "channel": "C12345",
                },
            }
        )

        signature = generate_slack_signature(body, timestamp, signing_secret)

        response = requests.post(
            function_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-slack-signature": signature,
                "x-slack-request-timestamp": timestamp,
            },
            timeout=30,
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
