#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
FRONTEND_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
IOS_APP_DIR="$FRONTEND_DIR/ios/App/App"
IOS_PROJECT_DIR="$FRONTEND_DIR/ios/App"
PBXPROJ_PATH="$IOS_PROJECT_DIR/App.xcodeproj/project.pbxproj"

if [ ! -d "$IOS_APP_DIR/public" ]; then
  echo "Xcode Cloud pre-xcodebuild failed: tracked ios/App/App/public is missing" >&2
  exit 1
fi

if [ ! -f "$IOS_APP_DIR/capacitor.config.json" ]; then
  echo "Xcode Cloud pre-xcodebuild failed: tracked ios/App/App/capacitor.config.json is missing" >&2
  exit 1
fi

if [ ! -f "$PBXPROJ_PATH" ]; then
  echo "Xcode Cloud pre-xcodebuild failed: App.xcodeproj/project.pbxproj is missing" >&2
  exit 1
fi

if ! grep -q 'CODE_SIGNING_ALLOWED = NO;' "$PBXPROJ_PATH"; then
  perl -0pi -e 's#(/\* Debug \*/ = \{\n\t\t\tisa = XCBuildConfiguration;\n\t\t\tbuildSettings = \{\n)#\1\t\t\t\tCODE_SIGNING_ALLOWED = NO;\n\t\t\t\tCODE_SIGNING_REQUIRED = NO;\n#g' "$PBXPROJ_PATH"
  echo "==> Xcode Cloud: disabled code signing for Debug configurations in the CI workspace"
fi

echo "==> Xcode Cloud: tracked Capacitor iOS assets verified before xcodebuild"
