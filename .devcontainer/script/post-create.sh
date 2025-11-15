#!/bin/bash
# Dev Container 起動後の初期化スクリプト
set -e  # エラーで停止

echo "================================================"
echo "Post-create setup starting..."
echo "================================================"

# mise のアクティベート
echo "Step 1: Activating mise..."
eval "$(~/.local/bin/mise activate bash)"
echo "✓ mise activated"

# mise trust の実行
echo "Step 2: Trusting mise config..."
mise trust || {
  echo "⚠ mise trust failed, but continuing..."
}
echo "✓ mise trust completed"

# Python 依存関係のインストール
echo "Step 3: Installing Python dependencies with uv..."
cd agent
uv sync
echo "✓ uv sync completed"

# pre-commit のインストール
echo "Step 4: Installing pre-commit..."
cd /workspaces/slack-issue-agent
uv pip install pre-commit
echo "✓ pre-commit installed"

# pre-commit hooks のセットアップ
echo "Step 5: Setting up pre-commit hooks..."
agent/.venv/bin/pre-commit install
echo "✓ pre-commit hooks installed"

# git-secrets のセットアップ
echo "Step 6: Setting up git-secrets..."
git secrets --install || {
  echo "⚠ git secrets --install failed (may already be installed)"
}
git secrets --register-aws || {
  echo "⚠ git secrets --register-aws failed (may already be registered)"
}
echo "✓ git-secrets setup completed"

echo "================================================"
echo "Post-create setup completed successfully!"
echo "================================================"
