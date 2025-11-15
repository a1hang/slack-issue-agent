"""CDK Bootstrap verification tests"""

import json
import subprocess

import pytest


def test_cdk_bootstrap_stack_exists():
    """Test that CDK Bootstrap stack exists in ap-northeast-1"""
    result = subprocess.run(
        [
            "aws",
            "cloudformation",
            "describe-stacks",
            "--stack-name",
            "CDKToolkit",
            "--region",
            "ap-northeast-1",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        pytest.skip("CDK Bootstrap not yet configured or AWS credentials not available")

    # Parse JSON output
    output = json.loads(result.stdout)
    stacks = output.get("Stacks", [])

    assert len(stacks) == 1, "CDKToolkit stack not found"
    stack = stacks[0]

    # Verify stack status
    assert (
        stack["StackStatus"] == "CREATE_COMPLETE" or stack["StackStatus"] == "UPDATE_COMPLETE"
    ), f"CDKToolkit stack is not in a healthy state: {stack['StackStatus']}"

    # Verify stack name
    assert stack["StackName"] == "CDKToolkit", "Stack name mismatch"


def test_cdk_bootstrap_outputs():
    """Test that CDK Bootstrap stack has required outputs"""
    result = subprocess.run(
        [
            "aws",
            "cloudformation",
            "describe-stacks",
            "--stack-name",
            "CDKToolkit",
            "--region",
            "ap-northeast-1",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        pytest.skip("CDK Bootstrap not yet configured or AWS credentials not available")

    output = json.loads(result.stdout)
    stacks = output.get("Stacks", [])
    stack = stacks[0]
    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}

    # Verify required outputs exist
    assert "BucketName" in outputs, "S3 bucket name output missing"
    assert "ImageRepositoryName" in outputs, "ECR repository name output missing"
    assert "BootstrapVersion" in outputs, "Bootstrap version output missing"

    # Verify output values are not empty
    assert outputs["BucketName"], "S3 bucket name is empty"
    assert outputs["ImageRepositoryName"], "ECR repository name is empty"
    assert outputs["BootstrapVersion"], "Bootstrap version is empty"

    # Verify bucket name format
    assert "cdk-" in outputs["BucketName"], "S3 bucket name format unexpected"
    assert "ap-northeast-1" in outputs["BucketName"], "S3 bucket not in Tokyo region"

    # Verify ECR repository name format
    assert "cdk-" in outputs["ImageRepositoryName"], "ECR repository name format unexpected"
    assert "ap-northeast-1" in outputs["ImageRepositoryName"], "ECR repository not in Tokyo region"

    # Bootstrap version should be a number
    bootstrap_version = int(outputs["BootstrapVersion"])
    assert bootstrap_version >= 1, "Bootstrap version should be at least 1"


def test_cdk_bootstrap_s3_bucket_exists():
    """Test that CDK Bootstrap S3 bucket exists and is accessible"""
    # First get the bucket name from stack outputs
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
        pytest.skip("CDK Bootstrap not yet configured or AWS credentials not available")

    bucket_name = result.stdout.strip()
    assert bucket_name, "Could not retrieve S3 bucket name"

    # Check if bucket exists (skip if no S3 permissions)
    result = subprocess.run(
        ["aws", "s3", "ls", f"s3://{bucket_name}", "--region", "ap-northeast-1"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if "AccessDenied" in result.stderr or "is not authorized" in result.stderr:
        pytest.skip(
            f"No S3 permissions to verify bucket {bucket_name}, "
            f"but it exists in CloudFormation outputs"
        )

    assert result.returncode == 0, f"CDK Bootstrap S3 bucket {bucket_name} is not accessible"


def test_cdk_bootstrap_ecr_repository_exists():
    """Test that CDK Bootstrap ECR repository exists"""
    # First get the repository name from stack outputs
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
        pytest.skip("CDK Bootstrap not yet configured or AWS credentials not available")

    repo_name = result.stdout.strip()
    assert repo_name, "Could not retrieve ECR repository name"

    # Check if repository exists
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
    )

    assert result.returncode == 0, f"CDK Bootstrap ECR repository {repo_name} does not exist"

    # Verify repository details
    output = json.loads(result.stdout)
    repositories = output.get("repositories", [])
    assert len(repositories) == 1, "ECR repository not found or multiple repositories returned"

    repo = repositories[0]
    assert repo["repositoryName"] == repo_name, "Repository name mismatch"
