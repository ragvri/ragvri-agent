#!/usr/bin/env bash
# Lint script for the code-review skill.
# Usage: bash skills/code-review/scripts/lint.sh <file>
#
# Runs ruff check and reports results.

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file_or_directory>"
    exit 1
fi

TARGET="$1"

echo "=== Ruff Lint Check ==="
echo "Target: $TARGET"
echo ""

# Run ruff check
if uv run ruff check "$TARGET" 2>&1; then
    echo ""
    echo "✅ No lint issues found."
else
    echo ""
    echo "❌ Lint issues found. Run 'uv run ruff check --fix $TARGET' to auto-fix."
fi
