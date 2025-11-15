"""Slack API client initialization and utilities"""

import os
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def create_slack_client(token: str | None = None) -> WebClient:
    """
    Create and return a Slack WebClient instance.

    Args:
        token: Slack bot token. If None, attempts to read from SLACK_BOT_TOKEN
               environment variable.

    Returns:
        WebClient: Initialized Slack client

    Raises:
        ValueError: If token is None or empty

    Example:
        >>> client = create_slack_client("xoxb-your-token")
        >>> # Or use environment variable
        >>> client = create_slack_client()
    """
    if token is None:
        token = os.environ.get("SLACK_BOT_TOKEN")

    if not token:
        raise ValueError(
            "Slack bot token is required. "
            "Please provide a token or set the SLACK_BOT_TOKEN environment variable."
        )

    return WebClient(token=token)


def verify_slack_auth(token: str | None = None) -> dict[str, Any]:
    """
    Verify Slack authentication by calling auth.test API.

    Args:
        token: Slack bot token. If None, uses SLACK_BOT_TOKEN environment variable.

    Returns:
        Dict containing authentication information:
            - ok: bool - Whether authentication succeeded
            - url: str - Workspace URL
            - team: str - Team name
            - user: str - Bot user name
            - team_id: str - Team ID
            - user_id: str - Bot user ID

    Raises:
        SlackApiError: If authentication fails
        ValueError: If token is missing

    Example:
        >>> result = verify_slack_auth("xoxb-your-token")
        >>> print(f"Authenticated as {result['user']} in {result['team']}")
    """
    client = create_slack_client(token)

    try:
        response = client.auth_test()
        # Ensure we return a dict (response.data can be dict or bytes)
        data = response.data
        if isinstance(data, dict):
            return data
        raise ValueError(f"Unexpected response type: {type(data)}")
    except SlackApiError as e:
        # Re-raise with more context
        error_msg = f"Slack authentication failed: {e.response['error']}"
        raise SlackApiError(message=error_msg, response=e.response) from e  # type: ignore[no-untyped-call]


def check_canvas_api_availability(token: str | None = None) -> dict[str, Any]:
    """
    Check if Canvas API is available for the authenticated workspace.

    Note: Canvas API requires a paid Slack plan. This function attempts to
    verify availability by checking bot permissions and workspace features.

    Args:
        token: Slack bot token. If None, uses SLACK_BOT_TOKEN environment variable.

    Returns:
        Dict containing:
            - available: bool - Whether Canvas API appears to be available
            - scopes: list - Bot token scopes
            - message: str - Informational message

    Raises:
        SlackApiError: If API call fails
        ValueError: If token is missing

    Example:
        >>> result = check_canvas_api_availability()
        >>> if result['available']:
        ...     print("Canvas API is available")
        >>> else:
        ...     print(f"Canvas API not available: {result['message']}")
    """
    client = create_slack_client(token)

    try:
        # Get bot info to check scopes
        auth_response = client.auth_test()
        data = auth_response.data
        if not isinstance(data, dict):
            raise ValueError(f"Unexpected response type: {type(data)}")
        bot_scopes = data.get("scope", "").split(",")

        # Check for Canvas-related scopes
        canvas_scopes = ["canvases:read", "canvases:write"]
        has_canvas_scopes = any(scope in bot_scopes for scope in canvas_scopes)

        if not has_canvas_scopes:
            return {
                "available": False,
                "scopes": bot_scopes,
                "message": (
                    "Canvas API scopes not found. "
                    "Please add 'canvases:read' and 'canvases:write' scopes to your Slack app."
                ),
            }

        # If scopes are present, assume API is available
        # Note: Actual Canvas API calls would confirm this, but require a paid plan
        return {
            "available": True,
            "scopes": bot_scopes,
            "message": (
                "Canvas API scopes are configured. "
                "Note: Canvas API requires a paid Slack plan to use."
            ),
        }

    except SlackApiError as e:
        return {
            "available": False,
            "scopes": [],
            "message": f"Failed to check Canvas API availability: {e.response['error']}",
        }


if __name__ == "__main__":
    """
    Simple command-line tool to verify Slack authentication and Canvas API availability.

    Usage:
        export SLACK_BOT_TOKEN=xoxb-your-token-here
        python -m slack_issue_agent.slack_client
    """
    import sys

    print("Slack API Client Verification")
    print("=" * 50)

    # Check for token
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("❌ SLACK_BOT_TOKEN environment variable not set")
        print("\nPlease set your Slack bot token:")
        print("  export SLACK_BOT_TOKEN=xoxb-your-token-here")
        sys.exit(1)

    # Verify authentication
    print("\n1. Verifying Slack authentication...")
    try:
        auth_result = verify_slack_auth(token)
        print("✅ Authentication successful!")
        print(f"   Workspace: {auth_result.get('team')}")
        print(f"   Bot User: {auth_result.get('user')}")
        print(f"   Team ID: {auth_result.get('team_id')}")
        print(f"   User ID: {auth_result.get('user_id')}")
    except (SlackApiError, ValueError) as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)

    # Check Canvas API availability
    print("\n2. Checking Canvas API availability...")
    try:
        canvas_result = check_canvas_api_availability(token)
        if canvas_result["available"]:
            print(f"✅ {canvas_result['message']}")
            print(f"   Scopes: {', '.join(canvas_result['scopes'])}")
        else:
            print(f"⚠️  {canvas_result['message']}")
            if canvas_result["scopes"]:
                print(f"   Current scopes: {', '.join(canvas_result['scopes'])}")
    except Exception as e:
        print(f"❌ Canvas API check failed: {e}")

    print("\n" + "=" * 50)
    print("Verification complete!")
