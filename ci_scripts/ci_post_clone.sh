#!/bin/sh
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

echo "==> Xcode Cloud: frontend dependencies and Capacitor iOS assets are ready"
