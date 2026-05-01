#!/bin/bash
set -euo pipefail

echo "==> Xcode Cloud: preparing frontend dependencies for Capacitor iOS build"

REPO_ROOT="${CI_WORKSPACE:-$(cd "$(dirname "$0")/.." && pwd)}"
FRONTEND_DIR="$REPO_ROOT/frontend"

cd "$FRONTEND_DIR"

if command -v corepack >/dev/null 2>&1; then
  corepack enable
fi

yarn install --frozen-lockfile
yarn run build:mobile:raw

if [ ! -d "$FRONTEND_DIR/ios/App/App/public" ]; then
  echo "Xcode Cloud prep failed: ios/App/App/public was not created" >&2
  exit 1
fi

if [ ! -f "$FRONTEND_DIR/ios/App/App/capacitor.config.json" ]; then
  echo "Xcode Cloud prep failed: ios/App/App/capacitor.config.json was not created" >&2
  exit 1
fi

echo "==> Xcode Cloud: frontend dependencies and Capacitor iOS assets are ready"
