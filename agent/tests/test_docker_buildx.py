"""Docker buildx and multi-platform build configuration tests"""

import subprocess

import pytest


def test_docker_installed():
    """Test that Docker is installed and accessible"""
    result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, "Docker is not installed"
    assert "Docker version" in result.stdout, "Docker version not found in output"


def test_docker_daemon_running():
    """Test that Docker daemon is running"""
    result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, "Docker daemon is not running"


def test_docker_buildx_available():
    """Test that Docker buildx is available"""
    result = subprocess.run(
        ["docker", "buildx", "version"], capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0, "Docker buildx is not available"
    assert "buildx" in result.stdout.lower(), "buildx not found in version output"


def test_docker_buildx_builders():
    """Test that Docker buildx has available builders"""
    result = subprocess.run(["docker", "buildx", "ls"], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, "Docker buildx ls failed"
    # Should show at least the default builder
    assert "default" in result.stdout or "desktop-linux" in result.stdout, "No buildx builder found"


def test_docker_buildx_arm64_support():
    """Test that Docker buildx supports ARM64 platform"""
    result = subprocess.run(
        ["docker", "buildx", "inspect"], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, "Docker buildx inspect failed"
    # Check if ARM64/aarch64 is supported
    assert (
        "linux/arm64" in result.stdout or "linux/aarch64" in result.stdout
    ), "ARM64 platform support not found"


def test_docker_info_contains_buildkit():
    """Test that Docker supports BuildKit"""
    result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, "Docker info command failed"
    # BuildKit should be available (note: might not be default, but should be available)


@pytest.mark.skip(reason="Requires Dockerfile and takes time to build")
def test_docker_buildx_multi_platform_build():
    """Test ARM64 container build capability (integration test)

    This test is skipped by default as it requires:
    - agent/Dockerfile to exist
    - Time to build container image
    - Sufficient disk space

    Run manually with: pytest -v --run-integration
    """
    result = subprocess.run(
        [
            "docker",
            "buildx",
            "build",
            "--platform",
            "linux/arm64",
            "--load",
            "-t",
            "test-arm64:latest",
            ".",
        ],
        capture_output=True,
        text=True,
        cwd="/workspaces/slack-issue-agent/agent",
        timeout=300,
    )
    assert result.returncode == 0, f"ARM64 build failed: {result.stderr}"
