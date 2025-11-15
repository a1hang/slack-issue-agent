# .devcontainer/Dockerfile
ARG NODE_VERSION=22
FROM node:${NODE_VERSION}

# システムパッケージインストール
RUN apt-get update && apt-get install -y \
    git procps sudo fzf zsh man-db unzip gnupg2 gh \
    jq nano vim curl wget make \
    && rm -rf /var/lib/apt/lists/*

# git-secrets インストール（機密情報コミット防止）
RUN git clone https://github.com/awslabs/git-secrets.git /tmp/git-secrets && \
    cd /tmp/git-secrets && \
    make install && \
    rm -rf /tmp/git-secrets

# 非 root ユーザー設定（node ユーザー）
RUN mkdir -p /usr/local/share/npm-global && \
    chown -R node:node /usr/local/share/npm-global

# node ユーザーにパスワードなし sudo を許可（docker-init.sh 用）
RUN echo "node ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# 作業ディレクトリ
WORKDIR /workspace
RUN chown -R node:node /workspace

# Claude 設定ディレクトリ（ホストからマウントされる）
RUN mkdir -p /home/node/.claude && chown -R node:node /home/node/.claude

# zsh デフォルトシェル設定
RUN chsh -s /bin/zsh node

# エディタ設定
ENV EDITOR=nano
ENV VISUAL=nano

# コマンド履歴永続化
RUN mkdir -p /commandhistory && \
    chown -R node:node /commandhistory

# git-delta インストール（差分表示を見やすく）
RUN ARCH=$(dpkg --print-architecture) && \
    wget https://github.com/dandavison/delta/releases/download/0.18.2/git-delta_0.18.2_${ARCH}.deb && \
    dpkg -i git-delta_0.18.2_${ARCH}.deb && \
    rm git-delta_0.18.2_${ARCH}.deb

# スクリプトをコピー
COPY ./script/install-mise.sh /usr/local/bin/install-mise.sh
COPY ./script/post-create.sh /usr/local/bin/post-create.sh
RUN chmod +x /usr/local/bin/install-mise.sh /usr/local/bin/post-create.sh

# mise を node ユーザーとしてインストール
RUN sudo -u node sh -c 'sh /usr/local/bin/install-mise.sh' \
  && mkdir -p /home/node/.local/share/mise \
  && chown -R node:node /home/node/.local/share

USER node

# mise で Node.js と Python をインストール
RUN bash -c '\
  eval "$(~/.local/bin/mise activate bash)"; \
  mise install -y; \
'

# uv (Python package manager) をインストール
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Claude Code CLI をインストール
RUN curl -fsSL https://claude.ai/install.sh | bash
