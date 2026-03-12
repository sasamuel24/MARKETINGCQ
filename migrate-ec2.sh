#!/bin/bash
# =============================================================================
# migrate-ec2.sh — Ejecutar en el EC2 directamente
# Uso: bash ~/MARKETINGCQ/migrate-ec2.sh
# =============================================================================

set -euo pipefail

REPO_PATH="/home/ubuntu/MARKETINGCQ"
BACKEND_PATH="/home/ubuntu/MARKETINGCQ/backend"
VENV_PATH="/home/ubuntu/MARKETINGCQ/backend/venv"
SERVICE_NAME="marketingcq"
BRANCH="main"

GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✔]${NC} $1"; }
fail() { echo -e "${RED}[✘]${NC} $1"; exit 1; }

echo ""
echo "=============================================="
echo "   MIGRACIÓN MARKETINGCQ — EC2"
echo "=============================================="
echo ""

# 1. Git pull
cd "$REPO_PATH"
git pull origin "$BRANCH"
log "Código actualizado"

# 2. Activar venv
source "$VENV_PATH/bin/activate"
log "Virtualenv activado"

# 3. Dependencias
cd "$BACKEND_PATH"
pip install -r requirements.txt --quiet
log "Dependencias OK"

# 4. Migraciones
alembic upgrade head
log "Migraciones aplicadas"

# 5. Reiniciar servicio
sudo systemctl restart "$SERVICE_NAME"
sleep 2
systemctl is-active --quiet "$SERVICE_NAME" \
    && log "Servicio '$SERVICE_NAME' corriendo" \
    || fail "El servicio no arrancó — revisa: sudo journalctl -u $SERVICE_NAME -n 30"

echo ""
log "LISTO — backend actualizado y BD migrada"
echo ""
