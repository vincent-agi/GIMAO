#!/bin/bash
# ============================================================
# Reinstallation GIMAO — Linux / macOS
#
# Equivalent de reinstall.bat pour systemes Unix.
# ATTENTION : supprime les donnees existantes.
# Usage : ./reinstall.sh   (ou bash reinstall.sh)
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

echo "Ce script va supprimer l'ancienne installation et reinstaller GIMAO proprement."
echo "ATTENTION : les donnees existantes seront effacees."
echo ""
read -p "Appuie sur Entree pour continuer (Ctrl+C pour annuler)..." _

if ! docker info > /dev/null 2>&1; then
    echo "ERREUR : Docker n'est pas lance."
    exit 1
fi

echo "[1/5] Arret et suppression de l'ancienne installation..."
docker compose -f docker-compose.prod.yml down -v > /dev/null 2>&1 || true
docker rmi aminata11/gimao-backend:latest aminata11/gimao-nginx:latest > /dev/null 2>&1 || true

echo "[2/5] Creation du fichier de configuration..."
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

echo "[3/5] Telechargement des nouvelles images..."
docker compose -f docker-compose.prod.yml pull

echo "[4/5] Demarrage de l'application..."
docker compose -f docker-compose.prod.yml up -d

echo "[5/5] Initialisation de la base de donnees (merci de patienter)..."
sleep 15
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend python manage.py init_data
docker compose -f docker-compose.prod.yml exec backend python manage.py seed_tp_data

sleep 3
open_browser "http://localhost"

echo ""
echo "L'application est prete sur http://localhost"
