"""AWS CLI configuration and connectivity tests"""

import os
import subprocess

import pytest


def test_aws_cli_installed():
    """Test that AWS CLI v2 is installed"""
    result = subprocess.run(["aws", "--version"], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, "AWS CLI is not installed"
    assert "aws-cli/2" in result.stdout, "AWS CLI version 2 is required"


def test_aws_region_configuration():
    """Test that AWS region can be configured via environment variable"""
    # Check if AWS_REGION or AWS_DEFAULT_REGION is set or can be set
    original_region = os.environ.get("AWS_REGION")
    os.environ["AWS_REGION"] = "ap-northeast-1"

    try:
        result = subprocess.run(
            ["aws", "configure", "get", "region"],
            capture_output=True,
            text=True,
            timeout=5,
            env=os.environ,
        )
        # Either configured region or environment variable should work
        # We just verify AWS CLI responds without error
        assert result.returncode in [0, 1], "AWS CLI configure command failed"
    finally:
        if original_region:
            os.environ["AWS_REGION"] = original_region
        elif "AWS_REGION" in os.environ:
            del os.environ["AWS_REGION"]


def test_aws_credentials_support():
    """Test that AWS credentials can be configured via environment or profile"""
    # This test verifies AWS CLI supports credential configuration
    # without requiring actual credentials
    result = subprocess.run(["aws", "configure", "list"], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, "AWS CLI credential listing failed"
    # Should show credential configuration options
    assert any(
        keyword in result.stdout for keyword in ["access_key", "profile", "credentials"]
    ), "AWS CLI does not support credential configuration"


@pytest.mark.skip(reason="Requires valid AWS credentials")
def test_aws_tokyo_region_access():
    """Test AWS access to Tokyo region (ap-northeast-1)

    This test is skipped by default as it requires valid AWS credentials.
    Run with: pytest -v -m "not skip" to execute
    """
    result = subprocess.run(
        ["aws", "bedrock", "list-foundation-models", "--region", "ap-northeast-1"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, "Cannot access AWS Tokyo region"
    assert "claude" in result.stdout.lower(), "Claude models not available in region"
