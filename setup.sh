#!/bin/bash
# ============================================================
# PolyPoly — Script de setup VPS (Ubuntu 22.04+)
# Lance ce script UNE SEULE FOIS sur ton VPS
# ============================================================

set -e
echo "=== PolyPoly Setup ==="

# --- Python 3.11+ ---
if ! python3 --version | grep -qE "3\.(11|12|13)"; then
    echo "Installation Python 3.11..."
    sudo apt-get update -qq
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
fi

# --- Environnement virtuel ---
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo "Venv créé"
fi

source venv/bin/activate

# --- Dépendances ---
pip install --upgrade pip -q
pip install -r requirements.txt

# --- Fichier .env ---
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edite le fichier .env avec tes vraies clés API:"
    echo "  nano .env"
    echo ""
fi

# --- Dossiers ---
mkdir -p data logs models

# --- Service systemd (optionnel) ---
if command -v systemctl &> /dev/null; then
    SERVICE_FILE="/etc/systemd/system/polypoly.service"
    WORK_DIR=$(pwd)
    USER=$(whoami)

    sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=PolyPoly Polymarket Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin
ExecStart=$WORK_DIR/venv/bin/python main.py
Restart=always
RestartSec=30
StandardOutput=append:$WORK_DIR/logs/polypoly.log
StandardError=append:$WORK_DIR/logs/polypoly_error.log

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    echo "Service systemd configuré: polypoly.service"
    echo ""
    echo "Commandes utiles:"
    echo "  sudo systemctl start polypoly    # Démarrer"
    echo "  sudo systemctl stop polypoly     # Arrêter"
    echo "  sudo systemctl enable polypoly   # Auto-démarrage au reboot"
    echo "  sudo systemctl status polypoly   # Statut"
    echo "  journalctl -u polypoly -f        # Logs live"
fi

echo ""
echo "=== Setup terminé ! ==="
echo ""
echo "Pour démarrer le bot:"
echo "  source venv/bin/activate"
echo "  python main.py"
