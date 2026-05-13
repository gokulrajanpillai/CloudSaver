#!/usr/bin/env bash
# Build, sign, notarize, and create DMG for CloudSaver macOS
set -euo pipefail

VERSION=$(cat cloudsaver/VERSION)
APP_NAME="CloudSaver"
BUNDLE_ID="app.cloudsaver.desktop"

echo "Building ${APP_NAME} ${VERSION} (${BUNDLE_ID})"

pyinstaller packaging/cloudsaver-desktop.spec --clean

codesign --deep --force --options runtime \
  --entitlements packaging/macos/entitlements.plist \
  --sign "${MACOS_DEVELOPER_ID}" \
  "dist/${APP_NAME}.app"

create-dmg \
  --volname "${APP_NAME} ${VERSION}" \
  --window-size 600 400 \
  --app-drop-link 450 185 \
  "dist/${APP_NAME}-${VERSION}.dmg" \
  "dist/${APP_NAME}.app"

xcrun notarytool submit "dist/${APP_NAME}-${VERSION}.dmg" \
  --apple-id "${APPLE_ID}" \
  --team-id "${APPLE_TEAM_ID}" \
  --password "${APPLE_APP_PASSWORD}" \
  --wait

xcrun stapler staple "dist/${APP_NAME}-${VERSION}.dmg"
echo "Build complete: dist/${APP_NAME}-${VERSION}.dmg"
