#!/usr/bin/env bash
# Build + start Odoo stack ở production mode.
# Chạy với user 'vbs' (đã có quyền docker từ 01-bootstrap-vm.sh).
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    cat > .env <<EOF
POSTGRES_PASSWORD=$(openssl rand -hex 16)
ODOO_MASTER_PASSWORD=$(openssl rand -hex 16)
ODOO_PORT=8069
EOF
    echo ">>> Đã tạo .env với password random. Lưu lại nội dung:"
    cat .env
    echo
fi

docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml pull || true
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build

echo
echo "Chờ Odoo healthy..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8069/web/database/selector >/dev/null 2>&1; then
        echo "Odoo đã chạy ở http://127.0.0.1:8069"
        break
    fi
    sleep 2
done

echo
echo "=== App up xong ==="
echo "Lần đầu? Init DB:"
echo "  docker compose exec odoo odoo -i vbs_base,vbs_garment,vbs_fabric,vbs_contact,vbs_planning,vbs_hr,vbs_config -d VBS_ERP --stop-after-init"
echo
echo "Logs:  docker compose logs -f odoo"
echo "Tiếp:  sudo bash deploy/03-nginx-https.sh <domain>"
