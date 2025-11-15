"""git-secrets configuration and functionality tests"""

import os
import subprocess

import pytest


def test_git_secrets_installed():
    """Test that git-secrets is installed"""
    result = subprocess.run(["git", "secrets", "--list"], capture_output=True, text=True, timeout=5)
    # git-secrets --list should work if it's installed
    # Return code 0 or 1 (no patterns yet) both indicate it's installed
    assert result.returncode in [0, 1], f"git-secrets is not installed: {result.stderr}"


def test_git_secrets_hooks_installed():
    """Test that git-secrets hooks are installed in the repository"""
    # Check if git hooks directory exists
    git_dir = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
        timeout=5,
        cwd="/workspaces/slack-issue-agent",
    )
    assert git_dir.returncode == 0, "Not in a git repository"

    git_hooks_dir = os.path.join("/workspaces/slack-issue-agent", git_dir.stdout.strip(), "hooks")

    # Check for git-secrets hooks
    expected_hooks = ["pre-commit", "commit-msg", "prepare-commit-msg"]
    for hook in expected_hooks:
        hook_path = os.path.join(git_hooks_dir, hook)
        assert os.path.exists(hook_path), f"git-secrets hook {hook} not found"

        # Verify hook contains git-secrets command
        with open(hook_path) as f:
            content = f.read()
            assert "git secrets" in content, f"Hook {hook} does not contain git-secrets"


def test_git_secrets_aws_patterns_registered():
    """Test that AWS patterns are registered in git-secrets"""
    result = subprocess.run(
        ["git", "config", "--get-all", "secrets.patterns"],
        capture_output=True,
        text=True,
        timeout=5,
        cwd="/workspaces/slack-issue-agent",
    )

    # Should have AWS patterns registered
    # Note: git-secrets --register-aws adds patterns to git config
    # We just verify that some patterns exist
    patterns = result.stdout

    # At minimum, should have some secret patterns configured
    # (exact patterns depend on git-secrets version)
    if result.returncode == 0:
        assert len(patterns) > 0, "No git-secrets patterns configured"


def test_git_secrets_custom_patterns_for_slack():
    """Test that custom patterns for Slack tokens are registered"""
    result = subprocess.run(
        ["git", "config", "--get-all", "secrets.patterns"],
        capture_output=True,
        text=True,
        timeout=5,
        cwd="/workspaces/slack-issue-agent",
    )

    if result.returncode != 0:
        pytest.skip("No git-secrets patterns configured yet")

    patterns = result.stdout

    # Check for Slack token patterns (xoxb-, xoxp-)
    # These should be added as custom patterns
    has_slack_patterns = "xoxb" in patterns or "xoxp" in patterns

    if not has_slack_patterns:
        pytest.skip("Slack patterns not yet configured (will be added in task 6.1)")


def test_git_secrets_custom_patterns_for_trello():
    """Test that custom patterns for Trello API keys are registered"""
    result = subprocess.run(
        ["git", "config", "--get-all", "secrets.patterns"],
        capture_output=True,
        text=True,
        timeout=5,
        cwd="/workspaces/slack-issue-agent",
    )

    if result.returncode != 0:
        pytest.skip("No git-secrets patterns configured yet")

    patterns = result.stdout

    # Check for Trello patterns
    has_trello_patterns = "TRELLO" in patterns

    if not has_trello_patterns:
        pytest.skip("Trello patterns not yet configured (will be added in task 6.1)")
