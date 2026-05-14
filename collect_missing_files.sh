#!/usr/bin/env bash

# =============================================================================
# Missing File Collector Script
# =============================================================================
# Purpose: Collect files from feature branches that are missing in main branch
# Usage: Run from repository root on main branch
# =============================================================================

set -euo pipefail

BRANCHES=(
    "Clasificación-y-Alteraciones-Morfológicas"
    "Validacion-y-Consistencia-Eventual"
    "Modelado-predictivo-caudal"
    "Adquisicion-de-datos-teledeteccion"
)

LOG_FILE="missing_files_log.txt"
COPIED_COUNT=0

echo "=============================================="
echo "Missing File Collector - Skyfusion Analytics"
echo "=============================================="
echo "Current branch: $(git branch --show-current)"
echo "Date: $(date)"
echo "=============================================="
echo ""

# Ensure log file exists (append mode)
touch "$LOG_FILE"

for BRANCH in "${BRANCHES[@]}"; do
    echo "Processing branch: $BRANCH"

    # Get list of files in branch
    FILES=$(git ls-tree -r "$BRANCH" --name-only)

    while IFS= read -r FILE; do
        if [ -z "$FILE" ]; then
            continue
        fi

        # Check if file exists in current working tree
        if [ ! -e "$FILE" ]; then
            # Create parent directories
            DIR=$(dirname "$FILE")
            if [ "$DIR" != "." ]; then
                mkdir -p "$DIR"
            fi

            # Copy file from branch
            git show "$BRANCH:$FILE" > "$FILE" 2>/dev/null

            # Log the copy
            echo "$FILE <- $BRANCH" >> "$LOG_FILE"
            echo "  + Copied: $FILE"
            COPIED_COUNT=$((COPIED_COUNT + 1))
        fi
    done <<< "$FILES"
done

echo ""
echo "=============================================="
echo "Summary"
echo "=============================================="
echo "Total files copied: $COPIED_COUNT"
echo ""
echo "Log saved to: $LOG_FILE"
echo ""

if [ $COPIED_COUNT -gt 0 ]; then
    echo "Files copied:"
    cat "$LOG_FILE"
else
    echo "No files were copied (all branches already merged)."
fi

echo ""
echo "Done!"