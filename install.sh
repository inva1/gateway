#!/bin/bash
set -e

echo "WiFi Manager Installer (with venv)"
echo "=================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running as pi
if [ "$USER" != "pi" ]; then
    echo -e "${RED}Please run as user 'pi' (not root or sudo)${NC}"
    exit 1
fi

# Paths
PROJECT_DIR="/home/pi/wifi-manager"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$BACKEND_DIR/venv"

echo -e "${GREEN}Updating system...${NC}"
sudo apt update && sudo apt upgrade -y

echo -e "${GREEN}Installing dependencies...${NC}"
sudo apt install -y python3-venv python3-pip mongodb network-manager nginx openssl

echo -e "${GREEN}Stopping conflicting services...${NC}"
sudo systemctl stop wpa_supplicant || true
sudo systemctl disable wpa_supplicant || true

echo -e "${GREEN}Cloning / updating project...${NC}"
if [ ! -d "$PROJECT_DIR" ]; then
    git clone https://github.com/yourname/wifi-manager.git "$PROJECT_DIR"
else
    cd "$PROJECT_DIR" && git pull
fi

cd "$PROJECT_DIR"

echo -e "${GREEN}Building React frontend...${NC}"
cd frontend
npm install
npm run build
cd ..

echo -e "${GREEN}Creating Python virtual environment...${NC}"
python3 -m venv "$VENV_DIR" --system-site-packages

echo -e "${GREEN}Installing Python packages in venv...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r backend/requirements.txt

echo -e "${GREEN}Generating SSL certificate...${NC}"
sudo mkdir -p /etc/ssl/private /etc/ssl/certs
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/wifi-manager.key \
    -out /etc/ssl/certs/wifi-manager.crt \
    -subj "/CN=raspberrypi.local" 2>/dev/null || true

echo -e "${GREEN}Installing systemd services...${NC}"
sudo cp backend/wifi-manager.service /etc/systemd/system/
sudo cp backend/wifi-autoconnect.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable wifi-manager.service
sudo systemctl enable wifi-autoconnect.service
sudo systemctl enable mongodb

echo -e "${GREEN}Starting services...${NC}"
sudo systemctl restart mongodb
sudo systemctl restart wifi-manager
sudo systemctl restart wifi-autoconnect

IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}"
echo "=================================================="
echo " WiFi Manager Installed Successfully!"
echo "=================================================="
echo " Access URL: https://$IP:8443"
echo " Username: admin"
echo " Password: raspberry123"
echo ""
echo " Change password in backend/main.py"
echo " Auto-connects to saved networks on boot"
echo " All data saved in MongoDB"
echo "=================================================="
echo -e "${NC}"