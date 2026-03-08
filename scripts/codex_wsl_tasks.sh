#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./codex_wsl_env.sh
source "$SCRIPT_DIR/codex_wsl_env.sh"

usage() {
  cat <<'EOF'
Usage: ./scripts/codex_wsl_tasks.sh <command> [args...]

Commands:
  bootstrap       Create or refresh the Linux-native Python and Node toolchains
  backend-test    Run pytest from the repo root
  frontend-test   Run the frontend Jest suite
  frontend-build  Run the frontend production build
  mainline-verify Run the full mainline validation ladder without installing deps
  compose-config  Render docker compose config
  compose-up      Run docker compose up with any extra args
  worker          Start the local Celery worker
  install-cli     Install the Codex CLI locally into .codex-tools/codex-cli
  codex           Run the repo-local or global Codex CLI with shared CODEX_HOME
  print-env       Print the active WSL Codex environment
EOF
}

ensure_wsl() {
  if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    return 0
  fi

  if grep -qi microsoft /proc/version 2>/dev/null; then
    return 0
  fi

  echo "This command is intended to run inside WSL." >&2
  exit 1
}

require_cmd() {
  local name="$1"

  if ! command -v "$name" >/dev/null 2>&1; then
    echo "Missing required command: $name" >&2
    exit 1
  fi
}

hash_file() {
  local file_path="$1"
  sha256sum "$file_path" | awk '{print $1}'
}

ensure_dirs() {
  mkdir -p \
    "$CODEX_WSL_REPO_ROOT/.tmp" \
    "$PIP_CACHE_DIR" \
    "$npm_config_cache" \
    "$PLAYWRIGHT_BROWSERS_PATH" \
    "$(dirname "$CODEX_WSL_CLI_PREFIX")"
}

activate_python_env() {
  export VIRTUAL_ENV="$CODEX_WSL_VENV_DIR"
  export PATH="$CODEX_WSL_VENV_DIR/bin:$PATH"
}

ensure_python_env() {
  local stamp_file requirements_hash

  require_cmd python3
  ensure_dirs

  if [[ ! -x "$CODEX_WSL_VENV_DIR/bin/python" ]]; then
    python3 -m venv "$CODEX_WSL_VENV_DIR"
  fi

  requirements_hash="$(hash_file "$CODEX_WSL_REPO_ROOT/requirements.txt")"
  stamp_file="$CODEX_WSL_VENV_DIR/.requirements.sha256"

  if [[ ! -f "$stamp_file" ]] || [[ "$(cat "$stamp_file")" != "$requirements_hash" ]]; then
    "$CODEX_WSL_VENV_DIR/bin/python" -m pip install --upgrade pip
    "$CODEX_WSL_VENV_DIR/bin/python" -m pip install -r "$CODEX_WSL_REPO_ROOT/requirements.txt"
    printf '%s\n' "$requirements_hash" > "$stamp_file"
  fi
}

ensure_frontend_deps() {
  local manifest_path manifest_hash stamp_file

  require_cmd npm
  ensure_dirs

  if [[ -f "$CODEX_WSL_REPO_ROOT/client/package-lock.json" ]]; then
    manifest_path="$CODEX_WSL_REPO_ROOT/client/package-lock.json"
  else
    manifest_path="$CODEX_WSL_REPO_ROOT/client/package.json"
  fi

  manifest_hash="$(hash_file "$manifest_path")"
  stamp_file="$CODEX_WSL_REPO_ROOT/client/node_modules/.codex-manifest.sha256"

  if [[ ! -f "$stamp_file" ]] || [[ "$(cat "$stamp_file")" != "$manifest_hash" ]]; then
    rm -rf "$CODEX_WSL_REPO_ROOT/client/node_modules"

    if [[ -f "$CODEX_WSL_REPO_ROOT/client/package-lock.json" ]]; then
      (
        cd "$CODEX_WSL_REPO_ROOT/client"
        npm ci
      )
    else
      (
        cd "$CODEX_WSL_REPO_ROOT/client"
        npm install
      )
    fi

    printf '%s\n' "$manifest_hash" > "$stamp_file"
  fi
}

require_existing_python_env() {
  require_cmd python3
  ensure_dirs

  if [[ ! -x "$CODEX_WSL_VENV_DIR/bin/python" ]]; then
    echo "Missing Python venv at $CODEX_WSL_VENV_DIR. Prepare the repo-local toolchain before running mainline verification." >&2
    exit 1
  fi

  activate_python_env
}

require_existing_frontend_deps() {
  require_cmd npm
  ensure_dirs

  if [[ ! -d "$CODEX_WSL_REPO_ROOT/client/node_modules" ]]; then
    echo "Missing frontend dependencies at $CODEX_WSL_REPO_ROOT/client/node_modules. Prepare the repo-local toolchain before running mainline verification." >&2
    exit 1
  fi
}

bootstrap() {
  ensure_wsl
  ensure_python_env
  activate_python_env
  ensure_frontend_deps
}

backend_test() {
  bootstrap
  cd "$CODEX_WSL_REPO_ROOT"
  pytest "$@"
}

frontend_test() {
  bootstrap
  cd "$CODEX_WSL_REPO_ROOT/client"

  if [[ "$#" -gt 0 ]]; then
    npm test -- "$@"
  else
    npm test -- --runInBand
  fi
}

frontend_build() {
  bootstrap
  cd "$CODEX_WSL_REPO_ROOT/client"
  npm run build -- "$@"
}

mainline_verify() {
  ensure_wsl
  require_existing_python_env
  require_existing_frontend_deps
  cd "$CODEX_WSL_REPO_ROOT"

  mkdir -p "$CODEX_WSL_REPO_ROOT/.tmp/pytest"
  export TMPDIR="$CODEX_WSL_REPO_ROOT/.tmp"

  "$CODEX_WSL_VENV_DIR/bin/python" -m flake8
  "$CODEX_WSL_VENV_DIR/bin/python" scripts/verify_translations.py
  DATABASE_URL=sqlite+aiosqlite:///./ci_migration.db \
    "$CODEX_WSL_VENV_DIR/bin/python" -m alembic upgrade head
  "$CODEX_WSL_VENV_DIR/bin/python" -m pytest tests -q -s \
    --basetemp "$CODEX_WSL_REPO_ROOT/.tmp/pytest"
  npm exec --prefix client tsc -- --noEmit --project client/tsconfig.json
  npm test --prefix client -- --runInBand
  npm run build --prefix client

  if npm exec --prefix client playwright -- --version >/dev/null 2>&1; then
    NODE_PATH="$CODEX_WSL_REPO_ROOT/client/node_modules" \
      npm exec --prefix client playwright -- test
  else
    echo "Playwright not available, skipping" >&2
  fi
}

docker_compose_cmd() {
  require_cmd docker

  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
    return
  fi

  echo "Docker Compose v2 is required (`docker compose`)." >&2
  exit 1
}

compose_config() {
  ensure_wsl
  cd "$CODEX_WSL_REPO_ROOT"
  docker_compose_cmd config "$@"
}

compose_up() {
  ensure_wsl
  cd "$CODEX_WSL_REPO_ROOT"
  docker_compose_cmd up "$@"
}

worker() {
  bootstrap
  cd "$CODEX_WSL_REPO_ROOT"
  exec ./scripts/start_worker.sh
}

install_cli() {
  ensure_wsl
  require_cmd npm
  ensure_dirs
  npm install --prefix "$CODEX_WSL_CLI_PREFIX" @openai/codex@latest
}

run_codex() {
  ensure_wsl

  if [[ -e "$CODEX_WSL_LOCAL_CODEX_BIN" ]]; then
    require_cmd node
    exec node "$CODEX_WSL_LOCAL_CODEX_BIN" "$@"
  fi

  if command -v codex >/dev/null 2>&1; then
    exec "$(command -v codex)" "$@"
  fi

  echo "Codex CLI not found. Run ./scripts/codex_wsl_tasks.sh install-cli or install it globally in WSL." >&2
  exit 1
}

print_env() {
  ensure_wsl
  cat <<EOF
CODEX_WSL_REPO_ROOT=$CODEX_WSL_REPO_ROOT
CODEX_HOME=$CODEX_HOME
CODEX_WSL_VENV_DIR=$CODEX_WSL_VENV_DIR
CODEX_WSL_CLI_PREFIX=$CODEX_WSL_CLI_PREFIX
PIP_CACHE_DIR=$PIP_CACHE_DIR
npm_config_cache=$npm_config_cache
PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH
EOF
}

main() {
  if [[ "$#" -eq 0 ]]; then
    usage
    exit 1
  fi

  local command="$1"
  shift

  case "$command" in
    bootstrap)
      bootstrap "$@"
      ;;
    backend-test)
      backend_test "$@"
      ;;
    frontend-test)
      frontend_test "$@"
      ;;
    frontend-build)
      frontend_build "$@"
      ;;
    mainline-verify)
      mainline_verify "$@"
      ;;
    compose-config)
      compose_config "$@"
      ;;
    compose-up)
      compose_up "$@"
      ;;
    worker)
      worker "$@"
      ;;
    install-cli)
      install_cli "$@"
      ;;
    codex)
      run_codex "$@"
      ;;
    print-env)
      print_env "$@"
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
