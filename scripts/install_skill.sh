#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
TARGET_DIR="$CODEX_HOME/skills/utoo-codex-pet"

required_files=(
  "SKILL.md"
  "scripts/utoo_watchdog.py"
  "scripts/install_utoo.sh"
  "assets/utoo/pet.json"
  "assets/utoo/spritesheet.webp"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$REPO_DIR/$file" ]]; then
    echo "Missing skill file: $REPO_DIR/$file" >&2
    exit 1
  fi
done

mkdir -p "$TARGET_DIR"

rsync -a --delete \
  --exclude ".git/" \
  --exclude ".DS_Store" \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  --exclude ".tmp-codex-home/" \
  --exclude "reports/*.log" \
  --exclude "reports/*.json" \
  --exclude "reports/*.md" \
  "$REPO_DIR/" "$TARGET_DIR/"

chmod +x "$TARGET_DIR/scripts/install_utoo.sh" "$TARGET_DIR/scripts/utoo_watchdog.py"

echo "Installed Utoo watchdog skill to: $TARGET_DIR"
echo "Use it in Codex as: \$utoo-codex-pet"
