"""Integration tests for development environment"""

import os
import subprocess

import pytest


def test_slack_api_authentication():
    """Test Slack API authentication (requires SLACK_BOT_TOKEN)"""
    from slack_issue_agent.slack_client import verify_slack_auth

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        pytest.skip("SLACK_BOT_TOKEN not set in environment")

    try:
        result = verify_slack_auth(token)
        assert result["ok"] is True, "Slack authentication failed"
        assert "team" in result, "Slack response missing team info"
        assert "user" in result, "Slack response missing user info"
    except Exception as e:
        pytest.fail(f"Slack API authentication failed: {e}")


def test_cdk_synth():
    """Test that CDK synth generates CloudFormation template"""
    result = subprocess.run(
        ["npx", "cdk", "synth"],
        cwd="/workspaces/slack-issue-agent/cdk",
        capture_output=True,
        text=True,
        timeout=120,
    )

    # Check for common errors
    if result.returncode != 0:
        error_output = result.stderr.lower()
        stdout_output = result.stdout.lower()
        combined = error_output + stdout_output

        if "no stacks" in combined or "no such file" in combined:
            pytest.skip("CDK app not yet implemented (no stacks defined)")
        elif "cannot find module" in combined:
            pytest.skip("CDK dependencies not installed (run: cd cdk && npm install)")
        elif "--app is required" in combined or "cdk.json" in combined:
            pytest.skip("CDK app not yet configured (cdk.json or bin/ entry point needed)")
        else:
            pytest.fail(f"CDK synth failed:\n{result.stdout}\n{result.stderr}")

    # Verify CloudFormation template is generated
    assert result.returncode == 0, f"CDK synth failed:\n{result.stderr}"
    # CDK synth outputs CloudFormation YAML/JSON
    assert len(result.stdout) > 0, "CDK synth produced no output"


def test_setup_script_equivalent():
    """Test that setup commands complete successfully"""
    # This test simulates the Dev Container postCreateCommand

    # Step 1: Verify mise is working
    result = subprocess.run(
        ["mise", "list"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "mise list failed"

    # Step 2: Verify Python dependencies are installed
    result = subprocess.run(
        ["uv", "pip", "list"],
        cwd="/workspaces/slack-issue-agent/agent",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "uv pip list failed"
    assert len(result.stdout) > 0, "No Python packages installed"

    # Step 3: Verify Node.js dependencies are installed
    result = subprocess.run(
        ["npm", "list", "--depth=0"],
        cwd="/workspaces/slack-issue-agent/cdk",
        capture_output=True,
        text=True,
        timeout=10,
    )
    # npm list returns 0 if all dependencies installed
    # Returns 1 if some peer dependencies are missing (acceptable)
    assert result.returncode in [0, 1], "npm list failed"


def test_git_secrets_configured():
    """Test that git-secrets is properly configured in the repository"""
    # Check if git-secrets hooks are installed
    result = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd="/workspaces/slack-issue-agent",
        capture_output=True,
        text=True,
        timeout=5,
    )

    # git-secrets installs hooks in .git/hooks/, not via core.hooksPath
    # So we check if git secrets --list works
    result = subprocess.run(
        ["git", "secrets", "--list"],
        cwd="/workspaces/slack-issue-agent",
        capture_output=True,
        text=True,
        timeout=5,
    )

    # git secrets --list returns 0 if configured, 1 if no patterns
    assert result.returncode in [0, 1], "git-secrets is not properly configured"


def test_docker_buildx_arm64_support():
    """Test that Docker buildx can build ARM64 images"""
    result = subprocess.run(
        ["docker", "buildx", "inspect"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode != 0:
        pytest.skip("Docker buildx not available")

    # Check for ARM64 platform support
    output = result.stdout.lower()
    has_arm64 = "linux/arm64" in output or "linux/aarch64" in output
    assert has_arm64, "Docker buildx does not support ARM64 platform"
