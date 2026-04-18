#!/usr/bin/env bash
# Cài nginx + certbot và bật HTTPS Let's Encrypt cho domain.
# Yêu cầu: domain đã trỏ A record về IP của VM trước khi chạy.
# Usage: sudo bash deploy/03-nginx-https.sh erp.example.com you@example.com
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Chạy với sudo: sudo bash $0 <domain> <email>"
    exit 1
fi

DOMAIN="${1:-}"
EMAIL="${2:-}"
if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: sudo bash $0 <domain> <email-cho-letsencrypt>"
    echo "  vd:  sudo bash $0 erp.vbs.vn admin@vbs.vn"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[1/4] Cài nginx + certbot..."
apt-get update -y
apt-get install -y nginx certbot python3-certbot-nginx

echo "[2/4] Kiểm tra DNS..."
VM_IP="$(curl -s https://api.ipify.org || hostname -I | awk '{print $1}')"
DOMAIN_IP="$(getent hosts "$DOMAIN" | awk '{print $1}' | head -n1 || true)"
echo "  VM IP:     $VM_IP"
echo "  $DOMAIN -> $DOMAIN_IP"
if [ "$VM_IP" != "$DOMAIN_IP" ]; then
    echo "  CẢNH BÁO: domain chưa trỏ về VM. Certbot có thể fail."
    read -p "  Tiếp tục? [y/N] " ans
    [ "$ans" = "y" ] || exit 1
fi

echo "[3/4] Tạo nginx vhost (HTTP-only trước để certbot challenge)..."
TMP_CONF="/etc/nginx/sites-available/vbs-erp"
cat > "$TMP_CONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    location /.well-known/acme-challenge/ { root /var/www/html; }
    location / { return 200 'ready for cert'; add_header Content-Type text/plain; }
}
EOF
ln -sf "$TMP_CONF" /etc/nginx/sites-enabled/vbs-erp
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "[4/4] Xin cert + áp dụng config full..."
certbot certonly --webroot -w /var/www/html \
    --non-interactive --agree-tos --email "$EMAIL" \
    -d "$DOMAIN"

# Áp template với domain thực
sed "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" \
    "$SCRIPT_DIR/nginx-vbs-erp.conf.template" > "$TMP_CONF"
nginx -t
systemctl reload nginx

# Auto-renew (certbot package đã setup systemd timer, kiểm tra)
systemctl enable --now certbot.timer

echo
echo "=== HTTPS xong ==="
echo "  https://$DOMAIN"
echo
echo "Cert sẽ tự renew. Test thử:"
echo "  sudo certbot renew --dry-run"
