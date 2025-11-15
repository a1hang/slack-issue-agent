"""Slack API client initialization and connectivity tests"""

import os
from unittest.mock import MagicMock, patch

import pytest


def test_slack_client_module_exists():
    """Test that slack_client module can be imported"""
    try:
        from slack_issue_agent import slack_client

        assert slack_client is not None
    except ImportError as e:
        pytest.fail(f"slack_client module not found: {e}")


def test_slack_client_initialization_with_token():
    """Test that Slack client can be initialized with a valid token"""
    from slack_issue_agent.slack_client import create_slack_client

    # Use a fake token for testing
    fake_token = "xoxb-test-token"
    client = create_slack_client(fake_token)

    assert client is not None
    assert hasattr(client, "auth_test")


def test_slack_client_raises_error_without_token():
    """Test that Slack client raises error when token is missing"""
    from slack_issue_agent.slack_client import create_slack_client

    with pytest.raises(ValueError, match="Slack bot token"):
        create_slack_client(None)

    with pytest.raises(ValueError, match="Slack bot token"):
        create_slack_client("")


@patch("slack_sdk.WebClient.auth_test")
def test_slack_client_authentication_success(mock_auth_test):
    """Test successful Slack authentication"""
    from slack_issue_agent.slack_client import verify_slack_auth

    # Mock successful auth response
    # The WebClient.auth_test() returns a SlackResponse with a .data attribute
    mock_response = MagicMock()
    mock_response.data = {
        "ok": True,
        "url": "https://example.slack.com/",
        "team": "Example Team",
        "user": "bot_user",
        "team_id": "T12345678",
        "user_id": "U12345678",
    }
    mock_auth_test.return_value = mock_response

    fake_token = "xoxb-test-token"
    result = verify_slack_auth(fake_token)

    assert result["ok"] is True
    assert "team" in result
    assert "user" in result


@patch("slack_sdk.WebClient.auth_test")
def test_slack_client_authentication_failure(mock_auth_test):
    """Test Slack authentication failure with clear error message"""
    from slack_sdk.errors import SlackApiError

    from slack_issue_agent.slack_client import verify_slack_auth

    # Mock authentication failure
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.data = {"ok": False, "error": "invalid_auth"}

    mock_auth_test.side_effect = SlackApiError(
        message="Invalid authentication", response=mock_response
    )

    fake_token = "xoxb-invalid-token"

    with pytest.raises(SlackApiError) as exc_info:
        verify_slack_auth(fake_token)

    assert (
        "authentication" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
    )


@pytest.mark.skip(reason="Requires valid Slack credentials")
def test_canvas_api_availability():
    """Test Canvas API availability (requires paid Slack plan)

    This test requires:
    - Valid SLACK_BOT_TOKEN environment variable
    - Slack workspace with paid plan (Canvas API access)
    - Bot token with canvases:read scope
    """
    from slack_issue_agent.slack_client import check_canvas_api_availability

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        pytest.skip("SLACK_BOT_TOKEN not set")

    result = check_canvas_api_availability(token)

    # Should return information about Canvas API availability
    assert isinstance(result, dict)
    assert "available" in result


def test_slack_client_error_messages_are_clear():
    """Test that error messages are informative"""
    from slack_issue_agent.slack_client import create_slack_client

    try:
        create_slack_client(None)
    except ValueError as e:
        error_message = str(e)
        # Error message should mention what's missing
        assert "token" in error_message.lower()
        # Error message should provide guidance
        assert "SLACK_BOT_TOKEN" in error_message or "environment" in error_message
