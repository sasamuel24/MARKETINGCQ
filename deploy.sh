#!/bin/bash
# =============================================================================
# deploy.sh — Sube cambios a GitHub y ejecuta migraciones en EC2
# Uso: bash deploy.sh
# Desde el directorio raíz del proyecto: C:\desarollos\MARKETINGCQ
# =============================================================================

set -euo pipefail

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
EC2_HOST="18.188.28.168"
EC2_USER="ubuntu"
KEY_FILE="./key-mercadeo.pem"
REPO_PATH="/home/ubuntu/MARKETINGCQ"
BACKEND_PATH="/home/ubuntu/MARKETINGCQ/backend"
VENV_PATH="/home/ubuntu/MARKETINGCQ/venv"
SERVICE_NAME="marketingcq"
BRANCH="main"
# ─────────────────────────────────────────────────────────────────────────────

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✔]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
fail() { echo -e "${RED}[✘]${NC} $1"; exit 1; }

[[ ! -f "$KEY_FILE" ]] && fail "No se encontró la llave PEM: $KEY_FILE"

echo ""
echo "=============================================="
echo "   DEPLOY MARKETINGCQ → PRODUCCIÓN"
echo "=============================================="
echo ""

# ── 1. Push a GitHub ──────────────────────────────────────────────────────────
log "Empujando código a GitHub (branch: $BRANCH)..."
git push origin "$BRANCH"
log "Código en GitHub. Amplify desplegará el frontend automáticamente."

# ── 2. EC2: git pull + migración + reinicio ───────────────────────────────────
log "Conectando a EC2 ($EC2_USER@$EC2_HOST)..."

ssh -i "$KEY_FILE" \
    -o StrictHostKeyChecking=no \
    -o IdentitiesOnly=yes \
    "$EC2_USER@$EC2_HOST" << REMOTE
set -euo pipefail

echo ""
echo "--- [EC2] Trayendo últimos cambios ---"
cd "$REPO_PATH"
git fetch origin
git pull origin $BRANCH
echo "Git pull OK"

echo ""
echo "--- [EC2] Activando virtualenv ---"
source "$VENV_PATH/bin/activate"

echo ""
echo "--- [EC2] Instalando dependencias (si hay nuevas) ---"
cd "$BACKEND_PATH"
pip install -r requirements.txt --quiet
echo "Dependencias OK"

echo ""
echo "--- [EC2] Ejecutando migraciones Alembic ---"
alembic upgrade head
echo "Migraciones OK"

echo ""
echo "--- [EC2] Reiniciando servicio $SERVICE_NAME ---"
sudo systemctl restart "$SERVICE_NAME"
sleep 2
systemctl is-active --quiet "$SERVICE_NAME" \
    && echo "Servicio '$SERVICE_NAME' corriendo." \
    || echo "AVISO: Verifica el servicio manualmente."

REMOTE

echo ""
log "=========================================="
log " DEPLOY COMPLETO"
log "=========================================="
echo ""
echo "  Frontend : AWS Amplify (auto-deploy en curso)"
echo "  Backend  : EC2 $EC2_HOST — código actualizado"
echo "  BD       : Migraciones Alembic aplicadas"
echo ""
