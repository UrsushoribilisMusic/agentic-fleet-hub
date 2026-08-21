#!/usr/bin/env bash
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
xcodegen generate
xcodebuild \
  -project Canis.xcodeproj \
  -scheme Canis \
  -destination 'platform=iOS Simulator,name=iPhone 17' \
  -skipPackagePluginValidation \
  build

echo "BUILD SUCCEEDED"
