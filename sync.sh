#!/usr/bin/env bash
# ==============================================================================
# Sardis High School Swim & Dive — GitHub Pages Sync Script
# ==============================================================================
# Exports latest Short Course Yards team records to records.json, updates
# index.html, and pushes changes to GitHub (origin main) to trigger automatic
# deployment of https://joshuarlang-eng.github.io/SHS_Tracker/
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="python3"
if [ -d "$SCRIPT_DIR/.venv" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
fi

echo "[*] Exporting Sardis High School Team Records..."
"$PYTHON_BIN" "$SCRIPT_DIR/export_records.py"

echo ""
echo "[*] Checking git repository status..."
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "[!] Not in a git repository. Exiting."
    exit 1
fi

# Stage record files, web widget, and data backup CSVs
git add records.json index.html static data/*.csv times/*.cl2 times/*.zip times/*.hy3 2>/dev/null || true

if ! git diff --cached --quiet; then
    COMMIT_MSG="data: update SHS team records [$(date +'%Y-%m-%d %H:%M')]"
    git commit -m "$COMMIT_MSG"
    
    echo "[*] Pushing to GitHub (origin main)..."
    if git push origin main; then
        echo "[✓] Successfully pushed to GitHub! Website will update in ~25 seconds."
        echo "    URL: https://joshuarlang-eng.github.io/SHS_Tracker/"
    else
        echo "[!] Warning: Git push failed. Please verify your internet or GitHub credentials."
        exit 1
    fi
else
    echo "[i] GitHub Pages is already up to date with the latest team records."
fi

echo ""
echo "[✓] Synchronization complete!"
