#!/bin/bash
# Setup git-secrets with custom patterns for Slack and Trello

set -e

echo "Setting up git-secrets..."

# Navigate to repository root
cd /workspaces/slack-issue-agent

# Check if git-secrets is already installed in this repo
if git config --get secrets.patterns > /dev/null 2>&1; then
    echo "⚠️  git-secrets patterns already configured. Skipping installation."
else
    # Install git-secrets hooks
    echo "Installing git-secrets hooks..."
    git secrets --install || echo "⚠️  git-secrets hooks may already be installed"
fi

# Register AWS patterns
echo "Registering AWS patterns..."
git secrets --register-aws || echo "⚠️  AWS patterns may already be registered"

# Add custom pattern for Slack Bot tokens (xoxb-)
echo "Adding Slack Bot token pattern..."
git secrets --add 'xoxb-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24}' 2>/dev/null || \
    echo "⚠️  Slack Bot token pattern may already exist"

# Add custom pattern for Slack User tokens (xoxp-)
echo "Adding Slack User token pattern..."
git secrets --add 'xoxp-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24}' 2>/dev/null || \
    echo "⚠️  Slack User token pattern may already exist"

# Add custom pattern for Slack App-level tokens (xapp-)
echo "Adding Slack App token pattern..."
git secrets --add 'xapp-[0-9]+-[A-Z0-9]+-[0-9]+-[a-z0-9]+' 2>/dev/null || \
    echo "⚠️  Slack App token pattern may already exist"

# Add custom pattern for Trello API Key
echo "Adding Trello API key pattern..."
git secrets --add 'TRELLO_API_KEY["\047]?\s*[:=]\s*["\047]?[a-f0-9]{32}' 2>/dev/null || \
    echo "⚠️  Trello API key pattern may already exist"

# Add custom pattern for Trello API Token
echo "Adding Trello API token pattern..."
git secrets --add 'TRELLO_API_TOKEN["\047]?\s*[:=]\s*["\047]?[a-f0-9]{64}' 2>/dev/null || \
    echo "⚠️  Trello API token pattern may already exist"

# Add allowed patterns for example files
echo "Adding allowed patterns for example files..."
git secrets --add --allowed '.env.example' 2>/dev/null || \
    echo "⚠️  .env.example allowed pattern may already exist"

git secrets --add --allowed 'your-token-here' 2>/dev/null || \
    echo "⚠️  'your-token-here' allowed pattern may already exist"

git secrets --add --allowed 'your-api-key-here' 2>/dev/null || \
    echo "⚠️  'your-api-key-here' allowed pattern may already exist"

echo "✅ git-secrets setup completed successfully!"

# List configured patterns
echo ""
echo "Configured patterns:"
git secrets --list
