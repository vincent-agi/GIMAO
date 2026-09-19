#!/bin/bash
# ============================================================
# Installation GIMAO — Linux / macOS
#
# Equivalent de install.bat pour systemes Unix.
# Usage : ./install.sh   (ou bash install.sh)
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
echo "          INSTALLATION GIMAO"
echo "=========================================="
echo ""

# Verification Docker
if ! docker info > /dev/null 2>&1; then
    echo "ERREUR : Docker n'est pas lance."
    echo "Lance Docker Desktop (ou le service Docker), attends qu'il soit pret,"
    echo "puis relance ce script."
    exit 1
fi

echo "[1/4] Creation du fichier de configuration..."
cat > .env.prod << 'EOF'
MYSQL_ROOT_PASSWORD=rootpass123
MYSQL_DATABASE=gimao
MYSQL_USER=gimao_user
MYSQL_PASSWORD=gimao_pass123
SECRET_KEY=django-insecure-tp-gimao-2026-xK8mP3qL9nR7vW2jH5tY1uA4sD6fG0cE
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=Admin1234!
DJANGO_SUPERUSER_EMAIL=admin@gimao.fr
EOF
cp .env.prod .env

echo ""
echo "[2/4] Telechargement des images..."
docker compose -f docker-compose.prod.yml pull

echo ""
echo "[3/4] Demarrage de l'application..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "[4/4] Initialisation de la base de donnees (merci de patienter)..."
sleep 15
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend python manage.py init_data

sleep 3
open_browser "http://localhost"

echo ""
echo "L'application est prete sur http://localhost"
