#!/bin/sh
set -eu

echo "==> Xcode Cloud: verifying tracked Capacitor iOS assets"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
FRONTEND_DIR="$REPO_ROOT/frontend"

if [ ! -d "$FRONTEND_DIR/ios/App/App/public" ]; then
  echo "Xcode Cloud prep failed: tracked ios/App/App/public directory is missing" >&2
  exit 1
fi

if [ ! -f "$FRONTEND_DIR/ios/App/App/capacitor.config.json" ]; then
  echo "Xcode Cloud prep failed: tracked ios/App/App/capacitor.config.json is missing" >&2
  exit 1
fi

echo "==> Xcode Cloud: tracked Capacitor iOS assets are present"
