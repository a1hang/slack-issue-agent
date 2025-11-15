"""Test AssumeRole functionality for dev-user"""

import json
import os
import subprocess

import pytest


def get_assumed_role_credentials():
    """Get temporary credentials by assuming DevUserCdkAccessRole"""
    result = subprocess.run(
        [
            "aws",
            "sts",
            "assume-role",
            "--role-arn",
            "arn:aws:iam::794587662786:role/DevUserCdkAccessRole",
            "--role-session-name",
            "pytest-session",
            "--duration-seconds",
            "900",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        pytest.skip(f"Cannot assume role: {result.stderr}")

    output = json.loads(result.stdout)
    credentials = output["Credentials"]

    return {
        "AWS_ACCESS_KEY_ID": credentials["AccessKeyId"],
        "AWS_SECRET_ACCESS_KEY": credentials["SecretAccessKey"],
        "AWS_SESSION_TOKEN": credentials["SessionToken"],
        "AWS_DEFAULT_REGION": "ap-northeast-1",
    }


def test_assume_role_success():
    """Test that dev-user can assume DevUserCdkAccessRole"""
    result = subprocess.run(
        [
            "aws",
            "sts",
            "assume-role",
            "--role-arn",
            "arn:aws:iam::794587662786:role/DevUserCdkAccessRole",
            "--role-session-name",
            "test-session",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, f"AssumeRole failed: {result.stderr}"

    output = json.loads(result.stdout)
    assert "Credentials" in output, "No credentials in response"
    assert "AssumedRoleUser" in output, "No AssumedRoleUser in response"

    # Verify assumed role ARN
    assumed_role_arn = output["AssumedRoleUser"]["Arn"]
    assert (
        "assumed-role/DevUserCdkAccessRole" in assumed_role_arn
    ), f"Unexpected assumed role ARN: {assumed_role_arn}"


def test_s3_access_with_assumed_role():
    """Test S3 access using assumed role credentials"""
    # Get temporary credentials
    env = get_assumed_role_credentials()

    # Get bucket name from CloudFormation
    result = subprocess.run(
        [
            "aws",
            "cloudformation",
            "describe-stacks",
            "--stack-name",
            "CDKToolkit",
            "--region",
            "ap-northeast-1",
            "--query",
            "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue",
            "--output",
            "text",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        pytest.skip("Cannot get CDK Bootstrap bucket name")

    bucket_name = result.stdout.strip()

    # Try to list S3 bucket with assumed role credentials
    result = subprocess.run(
        ["aws", "s3", "ls", f"s3://{bucket_name}/", "--region", "ap-northeast-1"],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, **env},
    )

    assert result.returncode == 0, f"S3 access failed with assumed role: {result.stderr}"


def test_ecr_access_with_assumed_role():
    """Test ECR access using assumed role credentials"""
    # Get temporary credentials
    env = get_assumed_role_credentials()

    # Get ECR repository name from CloudFormation
    result = subprocess.run(
        [
            "aws",
            "cloudformation",
            "describe-stacks",
            "--stack-name",
            "CDKToolkit",
            "--region",
            "ap-northeast-1",
            "--query",
            "Stacks[0].Outputs[?OutputKey=='ImageRepositoryName'].OutputValue",
            "--output",
            "text",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        pytest.skip("Cannot get CDK Bootstrap ECR repository name")

    repo_name = result.stdout.strip()

    # Try to describe ECR repository with assumed role credentials
    result = subprocess.run(
        [
            "aws",
            "ecr",
            "describe-repositories",
            "--repository-names",
            repo_name,
            "--region",
            "ap-northeast-1",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, **env},
    )

    assert result.returncode == 0, f"ECR access failed with assumed role: {result.stderr}"

    # Verify repository details
    output = json.loads(result.stdout)
    repositories = output.get("repositories", [])
    assert len(repositories) == 1, "ECR repository not found"
    assert repositories[0]["repositoryName"] == repo_name, "Repository name mismatch"
