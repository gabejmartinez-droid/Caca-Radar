#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"
IOS_APP_DIR="$FRONTEND_DIR/ios/App/App"

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

  echo "Xcode Cloud pre-xcodebuild failed: neither yarn nor corepack is available" >&2
  exit 127
}

if [ ! -d "$IOS_APP_DIR/public" ] || [ ! -f "$IOS_APP_DIR/capacitor.config.json" ]; then
  echo "==> Xcode Cloud: Capacitor iOS assets missing before xcodebuild; rebuilding mobile web assets"
  cd "$FRONTEND_DIR"
  run_yarn install --frozen-lockfile
  run_yarn run build:mobile:raw
fi

if [ ! -d "$IOS_APP_DIR/public" ]; then
  echo "Xcode Cloud pre-xcodebuild failed: ios/App/App/public is still missing" >&2
  exit 1
fi

if [ ! -f "$IOS_APP_DIR/capacitor.config.json" ]; then
  echo "Xcode Cloud pre-xcodebuild failed: ios/App/App/capacitor.config.json is still missing" >&2
  exit 1
fi

echo "==> Xcode Cloud: Capacitor iOS assets verified before xcodebuild"
