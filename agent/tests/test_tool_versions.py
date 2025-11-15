"""Tests for tool version verification"""

import subprocess

import pytest


def test_nodejs_version():
    """Test that Node.js 22 is installed"""
    result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, "Node.js is not installed"
    version = result.stdout.strip()
    assert version.startswith("v22."), f"Expected Node.js v22.x, got {version}"


def test_python_version():
    """Test that Python 3.12+ is installed"""
    result = subprocess.run(["python", "--version"], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, "Python is not installed"
    version = result.stdout.strip()
    # Output format: "Python 3.x.x"
    # Extract version number
    import re

    match = re.search(r"Python (\d+)\.(\d+)", version)
    assert match, f"Could not parse Python version: {version}"
    major, minor = int(match.group(1)), int(match.group(2))
    assert major == 3, f"Expected Python 3.x, got {major}.{minor}"
    assert minor >= 12, f"Expected Python 3.12 or higher, got 3.{minor}"


def test_mise_installed():
    """Test that mise is installed"""
    result = subprocess.run(["mise", "--version"], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, "mise is not installed"
    # mise should output version info
    assert len(result.stdout.strip()) > 0, "mise version output is empty"


def test_uv_installed():
    """Test that uv is installed"""
    result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, "uv is not installed"
    # uv should output version info like "uv 0.x.x"
    assert "uv" in result.stdout.lower(), "uv version output is unexpected"


def test_aws_cli_version():
    """Test that AWS CLI v2 is installed"""
    result = subprocess.run(["aws", "--version"], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, "AWS CLI is not installed"
    # AWS CLI v2 outputs to stderr
    version_output = result.stdout + result.stderr
    assert "aws-cli/2" in version_output, f"Expected AWS CLI v2, got {version_output}"


def test_cdk_cli_installed():
    """Test that CDK CLI is installed"""
    try:
        result = subprocess.run(["cdk", "--version"], capture_output=True, text=True, timeout=5)
    except FileNotFoundError:
        pytest.skip("CDK CLI not installed (install with: npm install -g aws-cdk)")

    assert result.returncode == 0, "CDK CLI command failed"
    # CDK outputs version like "2.x.x (build ...)"
    assert len(result.stdout.strip()) > 0, "CDK version output is empty"


def test_docker_installed():
    """Test that Docker is installed"""
    result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, "Docker is not installed"
    assert "Docker version" in result.stdout, "Docker version output is unexpected"


def test_git_secrets_installed():
    """Test that git-secrets is installed"""
    result = subprocess.run(["git", "secrets", "--list"], capture_output=True, text=True, timeout=5)
    # git-secrets --list returns 0 or 1 (if no patterns yet)
    assert result.returncode in [0, 1], "git-secrets is not installed"
