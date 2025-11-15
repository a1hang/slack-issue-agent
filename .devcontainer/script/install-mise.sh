#!/bin/sh
# mise インストールスクリプト (nodeユーザー用)

# mise のインストール
curl https://mise.run | sh

# bashrc に mise activation を追加
cat << 'EOS' >> ~/.bashrc
eval "$(~/.local/bin/mise activate bash)"
EOS

# zshrc に設定を追加 (コマンド履歴永続化 + mise activation + git hook 保護)
cat << 'EOS' >> ~/.zshrc
# コマンド履歴永続化
export HISTFILE=/commandhistory/.zsh_history

# mise activation
eval "$(~/.local/bin/mise activate zsh)"

# Git Hook バイパス防止 (AI Agentによる --no-verify の使用を防ぐ)
git() {
  if [[ "$*" == *"--no-verify"* ]]; then
    echo "ERROR: --no-verify is not allowed. Git hooks must be respected."
    return 1
  fi
  command git "$@"
}
EOS

# bashrc に git hook 保護を追加
cat << 'EOS' >> ~/.bashrc
# Git Hook バイパス防止
git() {
  if [[ "$*" == *"--no-verify"* ]]; then
    echo "ERROR: --no-verify is not allowed. Git hooks must be respected."
    return 1
  fi
  command git "$@"
}
EOS

echo "mise installation completed for user: $(whoami)"
