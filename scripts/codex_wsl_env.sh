#!/usr/bin/env bash

CODEX_WSL_ENV_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CODEX_WSL_REPO_ROOT="${CODEX_WSL_REPO_ROOT:-$(cd "$CODEX_WSL_ENV_SCRIPT_DIR/.." && pwd)}"

export CODEX_HOME="${CODEX_HOME:-/mnt/c/Users/Bear/.codex}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$CODEX_WSL_REPO_ROOT/.pip-cache}"
export npm_config_cache="${npm_config_cache:-$CODEX_WSL_REPO_ROOT/.npm-cache}"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$CODEX_WSL_REPO_ROOT/.playwright-wsl}"
export CODEX_WSL_VENV_DIR="${CODEX_WSL_VENV_DIR:-$CODEX_WSL_REPO_ROOT/.codex-venv-wsl}"
export CODEX_WSL_CLI_PREFIX="${CODEX_WSL_CLI_PREFIX:-$CODEX_WSL_REPO_ROOT/.codex-tools/codex-cli}"
export CODEX_WSL_LOCAL_CODEX_BIN="${CODEX_WSL_LOCAL_CODEX_BIN:-$CODEX_WSL_CLI_PREFIX/node_modules/.bin/codex}"