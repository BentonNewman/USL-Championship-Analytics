#!/usr/bin/env bash
# Archive current data/ parquets to ~/backups/asa-parquets/<date>/
# Run after update_parquets.py at season milestones (preseason, mid-season, end of season).
#
# Usage:
#   bash scripts/archive_parquets.sh
#   bash scripts/archive_parquets.sh "2026-end-of-regular-season"   # optional label

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"

LABEL="${1:-}"
DATE_STR="$(date +%Y-%m-%d)"
ARCHIVE_NAME="${DATE_STR}${LABEL:+-$LABEL}"
ARCHIVE_DIR="$HOME/backups/asa-parquets/$ARCHIVE_NAME"

if [ ! -d "$DATA_DIR" ] || [ -z "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then
    echo "No parquet files found in $DATA_DIR — run update_parquets.py first." >&2
    exit 1
fi

mkdir -p "$ARCHIVE_DIR"
cp "$DATA_DIR"/*.parquet "$ARCHIVE_DIR/"

echo "Archived to: $ARCHIVE_DIR"
ls -lh "$ARCHIVE_DIR"
