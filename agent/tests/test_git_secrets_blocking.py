"""git-secrets blocking functionality tests"""

import os
import subprocess
import tempfile

import pytest


def test_git_secrets_blocks_aws_access_key():
    """Test that git-secrets blocks commits containing AWS access keys"""
    # Create a temporary file with a fake AWS access key
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, dir="/workspaces/slack-issue-agent"
    ) as f:
        f.write("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n")
        f.write("AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n")
        temp_file = f.name

    try:
        # Try to add the file to git
        subprocess.run(
            ["git", "add", temp_file],
            cwd="/workspaces/slack-issue-agent",
            capture_output=True,
            timeout=5,
        )

        # Try to commit (should fail due to git-secrets)
        result = subprocess.run(
            ["git", "commit", "-m", "Test commit with secrets"],
            cwd="/workspaces/slack-issue-agent",
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Commit should fail
        assert result.returncode != 0, "git-secrets did not block commit with AWS keys"

        # Error message should mention the blocked pattern
        combined_output = result.stdout + result.stderr
        assert any(
            keyword in combined_output.lower() for keyword in ["secret", "prohibited", "found"]
        ), f"Error message does not indicate secret detection: {combined_output}"

    finally:
        # Clean up: remove file from git and filesystem
        subprocess.run(
            ["git", "reset", "HEAD", temp_file],
            cwd="/workspaces/slack-issue-agent",
            capture_output=True,
            timeout=5,
        )
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_git_secrets_blocks_slack_bot_token():
    """Test that git-secrets blocks commits containing Slack bot tokens"""
    # Create a temporary file with a fake Slack bot token
    # Note: Token format is intentionally broken to avoid GitHub Push Protection
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir="/workspaces/slack-issue-agent"
    ) as f:
        # Split token to avoid detection: "xoxb-" + "DUMMY-TOKEN-VALUE"
        token = "xoxb-" + "1111111111111-2222222222222-XXXXXXXXXXXXXXXXXXXXXX"
        f.write(f'SLACK_BOT_TOKEN = "{token}"\n')
        temp_file = f.name

    try:
        # Try to add and commit
        subprocess.run(
            ["git", "add", temp_file],
            cwd="/workspaces/slack-issue-agent",
            capture_output=True,
            timeout=5,
        )

        result = subprocess.run(
            ["git", "commit", "-m", "Test commit with Slack token"],
            cwd="/workspaces/slack-issue-agent",
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Commit should fail
        assert result.returncode != 0, "git-secrets did not block commit with Slack token"

    finally:
        # Clean up
        subprocess.run(
            ["git", "reset", "HEAD", temp_file],
            cwd="/workspaces/slack-issue-agent",
            capture_output=True,
            timeout=5,
        )
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_git_secrets_allows_example_files():
    """Test that git-secrets allows files with allowed patterns like .env.example"""
    # Use the existing .env.example file instead of creating a temporary one
    example_file = "/workspaces/slack-issue-agent/.env.example"

    if not os.path.exists(example_file):
        pytest.skip(".env.example file not found")

    # Check if the file contains allowed patterns
    with open(example_file) as f:
        content = f.read()

    # Verify it has placeholder values
    assert (
        "your-token-here" in content or "your-api-key-here" in content
    ), ".env.example should contain placeholder values"

    # Run git-secrets scan on the file
    result = subprocess.run(
        ["git", "secrets", "--scan", example_file],
        cwd="/workspaces/slack-issue-agent",
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Should pass (allowed patterns)
    # Note: Return code 0 means no secrets found (allowed patterns work)
    # Return code 1 means secrets found
    assert (
        result.returncode == 0
    ), f"git-secrets blocked .env.example file with allowed patterns: {result.stderr}"


def test_git_secrets_scan_command():
    """Test that git secrets --scan command works"""
    # Create a temporary file with a fake secret
    # Note: Using dummy value to avoid GitHub Push Protection
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, dir="/workspaces/slack-issue-agent"
    ) as f:
        # Use obviously fake hex string
        api_key = "0" * 32  # 32 zeros instead of realistic hex
        f.write(f"TRELLO_API_KEY={api_key}\n")
        temp_file = f.name

    try:
        # Run git secrets --scan on the file
        result = subprocess.run(
            ["git", "secrets", "--scan", temp_file],
            cwd="/workspaces/slack-issue-agent",
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should detect the secret (non-zero return code)
        assert result.returncode != 0, "git secrets --scan did not detect secret"

        # Output should indicate what was found
        combined_output = result.stdout + result.stderr
        assert len(combined_output) > 0, "No output from git secrets --scan"

    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_git_secrets_error_message_clarity():
    """Test that git-secrets provides clear error messages"""
    # Create a file with multiple secrets
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir="/workspaces/slack-issue-agent"
    ) as f:
        f.write('AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"\n')
        temp_file = f.name

    try:
        subprocess.run(
            ["git", "add", temp_file],
            cwd="/workspaces/slack-issue-agent",
            capture_output=True,
            timeout=5,
        )

        result = subprocess.run(
            ["git", "commit", "-m", "Test error message"],
            cwd="/workspaces/slack-issue-agent",
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should fail
        assert result.returncode != 0

        # Error message should be informative
        combined_output = result.stdout + result.stderr

        # Should indicate the type of issue (git-secrets provides clear error messages)
        assert any(
            keyword in combined_output.lower()
            for keyword in ["error", "prohibited", "pattern", "matched"]
        ), f"Error message is not clear about the issue: {combined_output}"

        # Should provide helpful mitigation suggestions
        assert (
            "mitigations" in combined_output.lower() or "allowed" in combined_output.lower()
        ), "Error message does not provide mitigation suggestions"

    finally:
        # Clean up
        subprocess.run(
            ["git", "reset", "HEAD", temp_file],
            cwd="/workspaces/slack-issue-agent",
            capture_output=True,
            timeout=5,
        )
        if os.path.exists(temp_file):
            os.remove(temp_file)
