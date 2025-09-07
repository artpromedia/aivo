# hadolint ignore=DL3007,DL3008
# Use Ubuntu LTS as base
FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    jq \
    python3.11 \
    python3.11-venv \
    python3.11-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.8.4
ENV PATH="/root/.local/bin:$PATH"

# Install Node.js 20.19.4
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs=20.19.4-1nodesource1 \
    && npm install -g npm@latest

# Install pnpm 9.x
RUN npm install -g pnpm@9

# Install yq
RUN wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 \
    && chmod +x /usr/local/bin/yq

# Install linters and tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # hadolint
    && wget -qO /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 \
    && chmod +x /usr/local/bin/hadolint \
    # yamllint
    && pip3 install yamllint \
    # actionlint
    && wget -qO /usr/local/bin/actionlint https://github.com/rhysd/actionlint/releases/latest/download/actionlint_linux_amd64.tar.gz \
    && tar -xzf actionlint_linux_amd64.tar.gz \
    && mv actionlint /usr/local/bin/ \
    && rm actionlint_linux_amd64.tar.gz \
    # trivy
    && wget -qO /usr/local/bin/trivy https://github.com/aquasecurity/trivy/releases/latest/download/trivy_latest_Linux-64bit.tar.gz \
    && tar -xzf trivy_latest_Linux-64bit.tar.gz \
    && mv trivy /usr/local/bin/ \
    && rm trivy_latest_Linux-64bit.tar.gz \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js tools, enable corepack, set Python default, and clean up
RUN npm install -g @stoplight/spectral-cli@^6 \
    && corepack enable \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
