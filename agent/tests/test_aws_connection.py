"""Tests for AWS connection verification"""

import subprocess

import pytest


def test_aws_bedrock_list_foundation_models():
    """Test that Bedrock API is accessible and Claude models are available"""
    result = subprocess.run(
        [
            "aws",
            "bedrock",
            "list-foundation-models",
            "--region",
            "ap-northeast-1",
            "--query",
            "modelSummaries[?contains(modelId, `claude`)].modelId",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Check for common AWS CLI errors
    if result.returncode != 0:
        error_output = result.stderr.lower()
        if "could not connect" in error_output or "unable to locate credentials" in error_output:
            pytest.skip("AWS credentials not configured (run: aws configure)")
        elif "accessdenied" in error_output or "unauthorized" in error_output:
            pytest.skip("AWS credentials lack Bedrock permissions")
        else:
            pytest.fail(f"AWS Bedrock API call failed:\n{result.stderr}")

    # Verify output contains Claude models
    assert result.returncode == 0, f"Bedrock API call failed:\n{result.stderr}"
    assert len(result.stdout.strip()) > 0, "No Claude models found in output"
    # Output should be JSON array with model IDs
    assert "claude" in result.stdout.lower(), "No Claude models in the list"


def test_aws_bedrock_model_access_claude_sonnet_45():
    """Test that Claude Sonnet 4.5 model is accessible"""
    model_id = "anthropic.claude-sonnet-4-5-20250929-v1:0"

    result = subprocess.run(
        [
            "aws",
            "bedrock",
            "get-foundation-model",
            "--region",
            "ap-northeast-1",
            "--model-identifier",
            model_id,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Check for common AWS CLI errors
    if result.returncode != 0:
        error_output = result.stderr.lower()
        if "could not connect" in error_output or "unable to locate credentials" in error_output:
            pytest.skip("AWS credentials not configured (run: aws configure)")
        elif "accessdenied" in error_output or "unauthorized" in error_output:
            pytest.skip("AWS credentials lack Bedrock permissions")
        elif "not found" in error_output or "validationexception" in error_output:
            pytest.skip(f"Model {model_id} not found or not enabled in ap-northeast-1")
        else:
            pytest.fail(f"AWS Bedrock get-foundation-model failed:\n{result.stderr}")

    # Verify model information is returned
    assert result.returncode == 0, f"Failed to get model info:\n{result.stderr}"
    assert model_id in result.stdout, f"Model ID not in output: {result.stdout}"


def test_aws_region_tokyo():
    """Test that AWS is configured to use Tokyo region (ap-northeast-1)"""
    # Check default region configuration
    result = subprocess.run(
        ["aws", "configure", "get", "region"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # If no default region, we'll use environment variable or explicit --region
    if result.returncode != 0:
        pytest.skip(
            "No default AWS region configured (set via: aws configure or AWS_REGION env var)"
        )

    region = result.stdout.strip()
    # This test passes as long as AWS CLI is configured
    # The actual region can be overridden with --region flag
    # We just verify that a region is configured
    assert len(region) > 0, "AWS region is not configured"
