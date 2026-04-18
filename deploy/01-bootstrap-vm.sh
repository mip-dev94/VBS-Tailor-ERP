#!/usr/bin/env bash
# One-time setup cho Viettel VM Ubuntu 22.04+ (chạy với sudo).
# Cài docker, mở firewall, bật swap, tạo user vbs.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Chạy với sudo: sudo bash $0"
    exit 1
fi

echo "[1/5] apt update + tools cơ bản..."
apt-get update -y
apt-get install -y curl git ca-certificates ufw fail2ban

echo "[2/5] Cài Docker engine + compose plugin..."
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
fi
# Đảm bảo có compose v2 plugin
apt-get install -y docker-compose-plugin || true
systemctl enable --now docker

echo "[3/5] Tạo user 'vbs' và thêm vào group docker..."
if ! id vbs >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" vbs
fi
usermod -aG docker vbs

echo "[4/5] Bật swap 2GB (VM 2GB RAM hay OOM khi import lớn)..."
if ! swapon --show | grep -q '/swapfile'; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    if ! grep -q '/swapfile' /etc/fstab; then
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' > /etc/sysctl.d/99-swappiness.conf
fi

echo "[5/5] Cấu hình firewall (chỉ mở SSH + HTTP + HTTPS)..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

systemctl enable --now fail2ban

echo
echo "=== Bootstrap xong ==="
echo "Tiếp theo:"
echo "  1. su - vbs"
echo "  2. git clone <repo-url> ~/ERP_Fashion"
echo "  3. cd ~/ERP_Fashion/odoo/custom_addons"
echo "  4. bash deploy/02-app-up.sh"
