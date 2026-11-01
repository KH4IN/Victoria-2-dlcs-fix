#!/bin/bash
# SessionStart: install the pinned rtk release (token-saving output filter) if missing.
# Only runs in Claude Code cloud sessions; verifies a hardcoded SHA-256 before installing.
set -euo pipefail
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
command -v rtk >/dev/null 2>&1 && exit 0
[ "$(uname -m)" = "x86_64" ] || exit 0
VERSION=v0.49.0
ASSET=rtk-x86_64-unknown-linux-musl.tar.gz
SHA256=7278231dfd7e6a730a4ab7f847b195bcf02289c2d57622b0dab75a6411100c8f
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/$ASSET" "https://github.com/rtk-ai/rtk/releases/download/$VERSION/$ASSET"
echo "$SHA256  $tmp/$ASSET" | sha256sum -c --quiet -
tar -xzf "$tmp/$ASSET" -C "$tmp"
install -m 0755 "$(find "$tmp" -type f -name rtk | head -1)" /usr/local/bin/rtk
