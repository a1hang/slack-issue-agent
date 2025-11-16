#!/usr/bin/env bash
# Build and push Docker image to Amazon ECR for AgentCore deployment
#
# Usage:
#   ./scripts/build-and-push-ecr.sh [tag]
#
# Environment variables:
#   AWS_REGION: AWS region (default: ap-northeast-1)
#   AWS_ACCOUNT_ID: AWS account ID (auto-detected if not set)
#   ECR_REPOSITORY: ECR repository name (default: slack-issue-agent)
#
# Example:
#   AWS_REGION=us-east-1 ./scripts/build-and-push-ecr.sh v1.0.0

set -euo pipefail

# Configuration
AWS_REGION="${AWS_REGION:-ap-northeast-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-slack-issue-agent}"
IMAGE_TAG="${1:-latest}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get AWS account ID
if [ -z "${AWS_ACCOUNT_ID:-}" ]; then
    log_info "Detecting AWS account ID..."
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        log_error "Failed to detect AWS account ID. Please set AWS_ACCOUNT_ID environment variable."
        exit 1
    fi
    log_info "Detected AWS account ID: $AWS_ACCOUNT_ID"
fi

# Build ECR URI
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"
IMAGE_URI="${ECR_URI}:${IMAGE_TAG}"

log_info "Configuration:"
log_info "  Region:       $AWS_REGION"
log_info "  Repository:   $ECR_REPOSITORY"
log_info "  Image tag:    $IMAGE_TAG"
log_info "  Image URI:    $IMAGE_URI"
echo

# Check Docker buildx
if ! docker buildx version &>/dev/null; then
    log_error "Docker buildx is not available. Please install Docker with buildx support."
    exit 1
fi

# Ensure buildx builder exists
if ! docker buildx inspect slack-agent-builder &>/dev/null; then
    log_info "Creating buildx builder 'slack-agent-builder'..."
    docker buildx create --name slack-agent-builder --use
else
    log_info "Using existing buildx builder 'slack-agent-builder'..."
    docker buildx use slack-agent-builder
fi

# Build Docker image for ARM64
log_info "Building Docker image for ARM64 platform..."
cd "$(dirname "$0")/.."  # Change to agent/ directory
docker buildx build \
    --platform linux/arm64 \
    --tag "$IMAGE_URI" \
    --tag "${ECR_URI}:latest" \
    --load \
    .

if [ $? -eq 0 ]; then
    log_info "Docker image built successfully"
else
    log_error "Docker build failed"
    exit 1
fi

# Login to ECR
log_info "Logging in to Amazon ECR..."
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

if [ $? -ne 0 ]; then
    log_error "ECR login failed"
    exit 1
fi

# Check if ECR repository exists
log_info "Checking if ECR repository exists..."
if ! aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &>/dev/null; then
    log_warn "ECR repository '$ECR_REPOSITORY' does not exist. Creating..."
    aws ecr create-repository \
        --repository-name "$ECR_REPOSITORY" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256

    # Set lifecycle policy (keep only last 10 images)
    aws ecr put-lifecycle-policy \
        --repository-name "$ECR_REPOSITORY" \
        --region "$AWS_REGION" \
        --lifecycle-policy-text '{
            "rules": [{
                "rulePriority": 1,
                "description": "Keep only last 10 images",
                "selection": {
                    "tagStatus": "any",
                    "countType": "imageCountMoreThan",
                    "countNumber": 10
                },
                "action": {
                    "type": "expire"
                }
            }]
        }'

    log_info "ECR repository created with image scanning and lifecycle policy"
fi

# Push images to ECR
log_info "Pushing image with tag '$IMAGE_TAG' to ECR..."
docker push "$IMAGE_URI"

if [ "$IMAGE_TAG" != "latest" ]; then
    log_info "Pushing image with tag 'latest' to ECR..."
    docker push "${ECR_URI}:latest"
fi

log_info "Successfully pushed Docker image to ECR"
echo
log_info "Image URIs:"
log_info "  Tagged:  $IMAGE_URI"
log_info "  Latest:  ${ECR_URI}:latest"
echo
log_info "Next steps:"
log_info "  1. Update CDK AgentCoreStack to use this image URI"
log_info "  2. Run: cd ../cdk && npm run cdk deploy"
