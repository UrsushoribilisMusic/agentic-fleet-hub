#!/bin/bash
# install_pocketbase.sh: download the PocketBase binary this engine is tested with.
# The migrations in pb_migrations/ use the PocketBase 0.22 JavaScript API.
set -euo pipefail
VERSION="${POCKETBASE_VERSION:-0.22.10}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "$(uname -s)" in Darwin) os=darwin ;; Linux) os=linux ;; *) echo "unsupported OS" >&2; exit 1 ;; esac
case "$(uname -m)" in arm64|aarch64) arch=arm64 ;; x86_64|amd64) arch=amd64 ;; *) echo "unsupported CPU" >&2; exit 1 ;; esac
url="https://github.com/pocketbase/pocketbase/releases/download/v${VERSION}/pocketbase_${VERSION}_${os}_${arch}.zip"
tmp="$(mktemp -d)"
echo "Downloading $url"
curl -fsSL "$url" -o "$tmp/pb.zip"
unzip -q -o "$tmp/pb.zip" pocketbase -d "$DIR"
rm -rf "$tmp"
chmod +x "$DIR/pocketbase"
"$DIR/pocketbase" --version
