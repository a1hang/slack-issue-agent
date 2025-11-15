"""Tests for CDK TypeScript build and lint verification"""

import subprocess

import pytest


def test_cdk_typescript_build():
    """Test that CDK TypeScript code compiles successfully"""
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd="/workspaces/slack-issue-agent/cdk",
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Check if build script exists
    if "missing script" in result.stderr.lower():
        pytest.skip("CDK build script not configured in package.json")

    assert result.returncode == 0, f"TypeScript build failed:\n{result.stdout}\n{result.stderr}"


def test_cdk_eslint_runs():
    """Test that ESLint runs on CDK code"""
    result = subprocess.run(
        ["npm", "run", "lint"],
        cwd="/workspaces/slack-issue-agent/cdk",
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Check if lint script exists
    if "missing script" in result.stderr.lower():
        pytest.skip("CDK lint script not configured in package.json")

    # ESLint returns 0 if no errors, 1 if errors found, 2 if configuration error
    # We accept both 0 (no errors) and 1 (errors found, but runs successfully)
    assert result.returncode in [0, 1], f"ESLint failed to run:\n{result.stdout}\n{result.stderr}"


def test_agent_ruff_check_runs():
    """Test that ruff check runs on Agent code"""
    result = subprocess.run(
        ["ruff", "check", "."],
        cwd="/workspaces/slack-issue-agent/agent",
        capture_output=True,
        text=True,
        timeout=30,
    )

    # ruff check returns 0 if no issues, 1 if issues found
    # We accept both as long as ruff runs successfully
    assert result.returncode in [
        0,
        1,
    ], f"ruff check failed to run:\n{result.stdout}\n{result.stderr}"


def test_agent_ruff_format_check():
    """Test that ruff format check runs on Agent code"""
    result = subprocess.run(
        ["ruff", "format", "--check", "."],
        cwd="/workspaces/slack-issue-agent/agent",
        capture_output=True,
        text=True,
        timeout=30,
    )

    # ruff format --check returns 0 if formatted, 1 if changes needed
    # We accept both as long as ruff runs successfully
    assert result.returncode in [
        0,
        1,
    ], f"ruff format check failed to run:\n{result.stdout}\n{result.stderr}"
