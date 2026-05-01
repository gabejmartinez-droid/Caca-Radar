#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IOS_APP_DIR="$FRONTEND_DIR/ios/App/App"

if [ ! -d "$IOS_APP_DIR/public" ] || [ ! -f "$IOS_APP_DIR/capacitor.config.json" ]; then
  echo "==> Xcode Cloud: Capacitor iOS assets missing before xcodebuild; rebuilding mobile web assets"
  cd "$FRONTEND_DIR"
  if command -v corepack >/dev/null 2>&1; then
    corepack enable
  fi
  yarn install --frozen-lockfile
  yarn run build:mobile:raw
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
