#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

run_yarn() {
  if command -v yarn >/dev/null 2>&1; then
    yarn "$@"
    return
  fi

  if command -v corepack >/dev/null 2>&1; then
    corepack enable
    corepack yarn "$@"
    return
  fi

  echo "Xcode Cloud prep failed: neither yarn nor corepack is available" >&2
  exit 127
}

echo "==> Xcode Cloud: preparing frontend dependencies for Capacitor iOS build"

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
