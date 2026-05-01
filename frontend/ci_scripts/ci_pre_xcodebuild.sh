#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
FRONTEND_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
IOS_APP_DIR="$FRONTEND_DIR/ios/App/App"

if [ ! -d "$IOS_APP_DIR/public" ]; then
  echo "Xcode Cloud pre-xcodebuild failed: tracked ios/App/App/public is missing" >&2
  exit 1
fi

if [ ! -f "$IOS_APP_DIR/capacitor.config.json" ]; then
  echo "Xcode Cloud pre-xcodebuild failed: tracked ios/App/App/capacitor.config.json is missing" >&2
  exit 1
fi

echo "==> Xcode Cloud: tracked Capacitor iOS assets verified before xcodebuild"
