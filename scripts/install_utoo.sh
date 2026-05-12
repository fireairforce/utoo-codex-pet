#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSET_DIR="$REPO_DIR/assets/utoo"

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
TARGET_DIR="$CODEX_HOME/pets/utoo"

required_files=(
  "pet.json"
  "spritesheet.webp"
  "spritesheet.png"
  "source-mapping.json"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$ASSET_DIR/$file" ]]; then
    echo "Missing bundled asset: $ASSET_DIR/$file" >&2
    exit 1
  fi
done

mkdir -p "$TARGET_DIR"

for file in "${required_files[@]}"; do
  cp "$ASSET_DIR/$file" "$TARGET_DIR/$file"
done

echo "Installed Utoo pet to: $TARGET_DIR"
echo "Restart Codex or refresh the pet list, then select: Utoo"
