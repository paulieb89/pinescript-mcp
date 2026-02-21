#!/bin/bash
# Sync Pine Script docs from main repo to MCP server bundled docs.
# Run this before publishing to PyPI to ensure bundled docs are up to date.
#
# Usage: ./sync-docs.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_SRC="$SCRIPT_DIR/../../docs"
DOCS_DST="$SCRIPT_DIR/src/pinescript_mcp/docs"

if [ ! -d "$DOCS_SRC" ]; then
    echo "Error: Source docs not found at $DOCS_SRC"
    exit 1
fi

echo "Syncing docs from $DOCS_SRC to $DOCS_DST..."

# Sync directories
rsync -av --delete "$DOCS_SRC/concepts/" "$DOCS_DST/concepts/"
rsync -av --delete "$DOCS_SRC/reference/" "$DOCS_DST/reference/"
rsync -av --delete "$DOCS_SRC/visuals/" "$DOCS_DST/visuals/"
rsync -av --delete "$DOCS_SRC/writing_scripts/" "$DOCS_DST/writing_scripts/"

# Sync manifest
cp "$DOCS_SRC/LLM_MANIFEST.md" "$DOCS_DST/"

echo "Done! Bundled docs updated."
