#!/usr/bin/env bash
# Build the Teams app package: apps/teams/appPackage/dist/magic-telemetry.zip
#
#   APP_ID=<azure app (client) id> apps/teams/appPackage/build.sh
set -euo pipefail

: "${APP_ID:?set APP_ID to the Azure app (client) ID}"
here="$(cd "$(dirname "$0")" && pwd)"
out="$here/dist"
mkdir -p "$out"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

sed "s/<APP_ID>/$APP_ID/g" "$here/manifest.json" > "$tmp/manifest.json"
cp "$here/color.png" "$here/outline.png" "$tmp/"
rm -f "$out/magic-telemetry.zip"
(cd "$tmp" && zip -q "$out/magic-telemetry.zip" manifest.json color.png outline.png)
echo "wrote $out/magic-telemetry.zip"
