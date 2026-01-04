#!/bin/bash
# Create DMG installer for Housekeeper
# Usage: ./create_dmg.sh <version> <arch>
# Example: ./create_dmg.sh 0.1.10 arm64

set -e

VERSION="${1:-unknown}"
ARCH="${2:-$(uname -m)}"
APP_PATH="dist/Housekeeper.app"
DMG_NAME="Housekeeper-${VERSION}-macos-${ARCH}"
DMG_DIR="dist/dmg"

echo "Creating DMG for Housekeeper ${VERSION} (${ARCH})..."

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: $APP_PATH not found. Run PyInstaller first."
    exit 1
fi

# Clean up previous DMG directory
rm -rf "$DMG_DIR"
mkdir -p "$DMG_DIR"

# Copy app bundle
cp -R "$APP_PATH" "$DMG_DIR/"

# Create Applications symlink for drag-and-drop install
ln -s /Applications "$DMG_DIR/Applications"

# Create DMG
echo "Creating DMG..."
hdiutil create -volname "Housekeeper" \
    -srcfolder "$DMG_DIR" \
    -ov -format UDZO \
    "dist/${DMG_NAME}.dmg"

# Clean up
rm -rf "$DMG_DIR"

echo "Created: dist/${DMG_NAME}.dmg"