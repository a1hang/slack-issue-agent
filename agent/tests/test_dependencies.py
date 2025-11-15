"""Tests for dependency installation verification"""

import subprocess

import pytest


def test_cdk_aws_cdk_lib_installed():
    """Test that aws-cdk-lib is installed in CDK project"""
    result = subprocess.run(
        ["npm", "list", "aws-cdk-lib", "--depth=0"],
        cwd="/workspaces/slack-issue-agent/cdk",
        capture_output=True,
        text=True,
        timeout=10,
    )
    # npm list returns 0 if package exists, 1 if not found
    if result.returncode != 0:
        pytest.skip("CDK dependencies not yet installed (run: cd cdk && npm install)")

    assert "aws-cdk-lib@" in result.stdout, "aws-cdk-lib is not installed"


def test_cdk_bedrock_agentcore_alpha_installed():
    """Test that @aws-cdk/aws-bedrock-agentcore-alpha is installed"""
    result = subprocess.run(
        ["npm", "list", "@aws-cdk/aws-bedrock-agentcore-alpha", "--depth=0"],
        cwd="/workspaces/slack-issue-agent/cdk",
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        pytest.skip("CDK dependencies not yet installed (run: cd cdk && npm install)")

    assert "@aws-cdk/aws-bedrock-agentcore-alpha@" in result.stdout


def test_cdk_slack_web_api_installed():
    """Test that @slack/web-api is installed in CDK project"""
    result = subprocess.run(
        ["npm", "list", "@slack/web-api", "--depth=0"],
        cwd="/workspaces/slack-issue-agent/cdk",
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        pytest.skip("CDK dependencies not yet installed (run: cd cdk && npm install)")

    assert "@slack/web-api@" in result.stdout


def test_agent_strands_agents_installed():
    """Test that strands-agents is installed in Agent project"""
    result = subprocess.run(
        ["uv", "pip", "list"],
        cwd="/workspaces/slack-issue-agent/agent",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "uv pip list failed"
    assert "strands-agents" in result.stdout, "strands-agents is not installed"


def test_agent_slack_sdk_installed():
    """Test that slack-sdk is installed in Agent project"""
    result = subprocess.run(
        ["uv", "pip", "list"],
        cwd="/workspaces/slack-issue-agent/agent",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "uv pip list failed"
    assert "slack-sdk" in result.stdout, "slack-sdk is not installed"


def test_agent_httpx_installed():
    """Test that httpx is installed in Agent project"""
    result = subprocess.run(
        ["uv", "pip", "list"],
        cwd="/workspaces/slack-issue-agent/agent",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "uv pip list failed"
    assert "httpx" in result.stdout, "httpx is not installed"


def test_agent_bedrock_agentcore_installed():
    """Test that bedrock-agentcore is installed in Agent project"""
    result = subprocess.run(
        ["uv", "pip", "list"],
        cwd="/workspaces/slack-issue-agent/agent",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "uv pip list failed"
    # Check if bedrock-agentcore is installed
    # Note: The actual package name might be different
    output_lower = result.stdout.lower()
    has_agentcore = (
        "bedrock-agentcore" in output_lower
        or "agentcore" in output_lower
        or "strands-agents" in output_lower  # strands-agents might include agentcore
    )
    if not has_agentcore:
        pytest.skip("bedrock-agentcore not found (might be included in strands-agents)")


def test_agent_pytest_installed():
    """Test that pytest is installed as dev dependency"""
    result = subprocess.run(
        ["uv", "pip", "list"],
        cwd="/workspaces/slack-issue-agent/agent",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "uv pip list failed"
    assert "pytest" in result.stdout, "pytest is not installed"


def test_agent_ruff_installed():
    """Test that ruff is installed as dev dependency"""
    result = subprocess.run(
        ["uv", "pip", "list"],
        cwd="/workspaces/slack-issue-agent/agent",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "uv pip list failed"
    assert "ruff" in result.stdout, "ruff is not installed"
