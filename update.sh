#!/bin/bash
# ============================================================
# Mise a jour GIMAO — Linux / macOS
#
# Equivalent de update.bat pour systemes Unix.
# Usage : ./update.sh   (ou bash update.sh)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

open_browser() {
    URL="$1"
    if command -v open > /dev/null 2>&1; then
        open "$URL"        # macOS
    elif command -v xdg-open > /dev/null 2>&1; then
        xdg-open "$URL"    # Linux
    else
        echo "  Ouvre ton navigateur sur $URL"
    fi
}

echo ""
echo "=========================================="
echo "           MISE A JOUR GIMAO"
echo "=========================================="
echo ""

if ! docker info > /dev/null 2>&1; then
    echo "ERREUR : Docker n'est pas lance."
    exit 1
fi

echo "Telechargement de la nouvelle version..."
docker compose -f docker-compose.prod.yml pull

echo ""
echo "Redemarrage de l'application..."
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "=========================================="
echo "         MISE A JOUR TERMINEE !"
echo "=========================================="
echo ""
sleep 3
open_browser "http://localhost"
