#!/bin/bash
set -euo pipefail

echo "==> Xcode Cloud: preparing frontend dependencies for Capacitor iOS build"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"

run_yarn() {
  echo "==> Xcode Cloud: checking package managers"
  command -v node >/dev/null 2>&1 && echo "node: $(command -v node)" || true
  command -v npm >/dev/null 2>&1 && echo "npm: $(command -v npm)" || true
  command -v yarn >/dev/null 2>&1 && echo "yarn: $(command -v yarn)" || true
  command -v corepack >/dev/null 2>&1 && echo "corepack: $(command -v corepack)" || true
  command -v npx >/dev/null 2>&1 && echo "npx: $(command -v npx)" || true

  if command -v yarn >/dev/null 2>&1; then
    yarn "$@"
    return
  fi

  if command -v corepack >/dev/null 2>&1; then
    corepack enable
    corepack yarn "$@"
    return
  fi

  if command -v npx >/dev/null 2>&1; then
    npx --yes yarn@1.22.22 "$@"
    return
  fi

  echo "Xcode Cloud prep failed: no usable yarn runner found (yarn/corepack/npx unavailable)" >&2
  exit 127
}

cd "$FRONTEND_DIR"

run_yarn install --frozen-lockfile
run_yarn run build:mobile:raw

if [ ! -d "$FRONTEND_DIR/ios/App/App/public" ]; then
  echo "Xcode Cloud prep failed: ios/App/App/public was not created" >&2
  exit 1
fi

if [ ! -f "$FRONTEND_DIR/ios/App/App/capacitor.config.json" ]; then
  echo "Xcode Cloud prep failed: ios/App/App/capacitor.config.json was not created" >&2
  exit 1
fi

echo "==> Xcode Cloud: frontend dependencies and Capacitor iOS assets are ready"
