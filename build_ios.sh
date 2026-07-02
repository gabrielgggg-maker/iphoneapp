#!/bin/bash
# Build script for GelDroid iOS - run this on a Mac with Xcode installed
# Requirements: macOS, Xcode 15+, Flutter in PATH

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/geldroid" && pwd)"
cd "$PROJECT_DIR"

echo "=== GelDroid iOS Build ==="
echo "Flutter version:"
flutter --version

echo ""
echo "Installing dependencies..."
flutter pub get

echo ""
echo "Building IPA (no code signing - for AltStore/Sideloadly)..."
flutter build ipa --no-codesign

echo ""
echo "=== Done! ==="
echo "IPA location: build/ios/ipa/geldroid.ipa"
echo ""
echo "To install without App Store, use:"
echo "  - AltStore: https://altstore.io"
echo "  - Sideloadly: https://sideloadly.io"
