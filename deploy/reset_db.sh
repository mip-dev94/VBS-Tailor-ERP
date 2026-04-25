#!/usr/bin/env bash
# Xoá toàn bộ database và khởi tạo lại từ đầu.
# Chạy qua GitHub Actions workflow "Reset DB" với xác nhận "RESET".
set -euo pipefail

cd "$(dirname "$0")/.."

DB="${VBS_DB:-VBS_ERP}"
COMPOSE="docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml"

MODULES="vbs_base,vbs_config,vbs_contact,vbs_fabric,vbs_garment,vbs_hr,vbs_planning,vbs_product"

echo "=== [1/4] Backup DB lần cuối trước khi xoá ==="
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$HOME/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/${DB}_BEFORE_RESET_${TS}.sql.gz"
$COMPOSE exec -T db pg_dump -U odoo --no-owner --no-privileges "$DB" \
    | gzip > "$BACKUP_FILE" 2>/dev/null || echo "    (Backup thất bại hoặc DB chưa tồn tại, bỏ qua)"
echo "    → $BACKUP_FILE"

echo
echo "=== [2/4] Xoá database cũ ==="
$COMPOSE stop odoo 2>/dev/null || true
$COMPOSE up -d db
sleep 5
$COMPOSE exec -T db psql -U odoo postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB';" \
    2>/dev/null || true
$COMPOSE exec -T db psql -U odoo postgres \
    -c "DROP DATABASE IF EXISTS \"$DB\";" 2>&1
$COMPOSE exec -T db psql -U odoo postgres \
    -c "CREATE DATABASE \"$DB\" OWNER odoo ENCODING 'UTF8';" 2>&1
echo "    Database $DB đã được tạo mới (trống)"

echo
echo "=== [3/4] Khởi tạo Odoo với tất cả modules VBS ==="
PG_PASS=$(grep '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)
MASTER_PASS=$(grep '^ODOO_MASTER_PASSWORD=' .env | cut -d= -f2-)
sed -i "s|^db_password *=.*|db_password = $PG_PASS|" odoo.conf.docker
sed -i "s|^admin_passwd *=.*|admin_passwd = $MASTER_PASS|" odoo.conf.docker

$COMPOSE exec -T db pg_isready -U odoo -d "$DB" || sleep 5

# Init DB với tất cả modules
$COMPOSE run --rm odoo odoo \
    -i "$MODULES" \
    -d "$DB" \
    --stop-after-init \
    --logfile=/dev/stdout \
    --log-level=warn \
    --without-demo=all 2>&1

echo
echo "=== [4/4] Khởi động Odoo ==="
$COMPOSE up -d
sleep 8
curl -sI http://127.0.0.1:8069/web/login | head -1 || true

echo
echo "=== Reset xong ==="
echo "    Database: $DB (trắng tinh)"
echo "    Admin password: $MASTER_PASS"
echo "    URL: https://vbstailor-erp.online"
echo "    Backup cuối cùng: $BACKUP_FILE"
