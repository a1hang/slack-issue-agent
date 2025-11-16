# Multi-stage Dockerfile for AWS Bedrock AgentCore Runtime deployment
# Platform: ARM64 (required by AgentCore Runtime)
# Base: uv's official ARM64 Python image for fast dependency installation

# Stage 1: Build stage - Install dependencies
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /build

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv (faster than pip)
# --frozen: Use exact versions from lock file (if exists)
# --no-cache: Don't cache downloads to reduce image size
RUN uv sync --frozen --no-cache || uv sync --no-cache

# Stage 2: Runtime stage - Minimal production image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /build/.venv /app/.venv

# Copy dependency files (required for uv run)
COPY pyproject.toml ./

# Copy agent source code
COPY src/slack_issue_agent ./src/slack_issue_agent

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1

# Expose AgentCore Runtime required port
EXPOSE 8080

# Health check endpoint (required by AgentCore)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ping || exit 1

# Run application using uv
# AgentCore Runtime expects HTTP server at port 8080 with /invocations endpoint
CMD ["uv", "run", "python", "-m", "slack_issue_agent.agentcore_app"]
