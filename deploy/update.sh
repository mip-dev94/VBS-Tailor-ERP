#!/usr/bin/env bash
# Update Odoo: backup → pull → detect module thay đổi → migrate → restart.
# Idempotent — chạy lại không sao.
# Usage: bash deploy/update.sh         # auto-detect modules
#        bash deploy/update.sh all     # force update tất cả
set -euo pipefail

cd "$(dirname "$0")/.."

DB="${VBS_DB:-VBS_ERP}"
BACKUP_DIR="$HOME/backups"
mkdir -p "$BACKUP_DIR"

COMPOSE="docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml"

echo "=== [1/5] Backup DB trước update ==="
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB}_${TS}.sql.gz"
$COMPOSE exec -T db pg_dump -U odoo --no-owner --no-privileges "$DB" | gzip > "$BACKUP_FILE"
echo "    → $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
# Giữ 7 backup gần nhất
ls -1t "$BACKUP_DIR"/${DB}_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm -v

echo
echo "=== [2/5] Git pull ==="
OLD_SHA=$(git rev-parse HEAD)
git pull --ff-only
NEW_SHA=$(git rev-parse HEAD)
if [ "$OLD_SHA" = "$NEW_SHA" ]; then
    echo "    Không có commit mới. Bỏ qua restart."
    exit 0
fi
echo "    $OLD_SHA → $NEW_SHA"

echo
echo "=== [3/5] Detect module thay đổi ==="
if [ "${1:-}" = "all" ]; then
    MODULES="all"
    echo "    Force update tất cả module (--upgrade-all)."
else
    # Lấy thư mục con cấp 1 trong commits mới (= tên module)
    CHANGED=$(git diff --name-only "$OLD_SHA" "$NEW_SHA" \
        | grep -E '^vbs_[a-z_]+/' \
        | cut -d/ -f1 | sort -u | tr '\n' ',' | sed 's/,$//')
    if [ -z "$CHANGED" ]; then
        echo "    Không có module nào thay đổi. Chỉ rebuild + restart."
        MODULES=""
    else
        MODULES="$CHANGED"
        echo "    Module thay đổi: $MODULES"
    fi
fi

echo
echo "=== [4/5] Rebuild image (nếu Dockerfile/requirements đổi) ==="
$COMPOSE build odoo

echo
echo "=== [5/5] Sync conf + migrate + restart ==="
# Sync lại conf (phòng khi .env hoặc template đổi)
PG_PASS=$(grep '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)
MASTER_PASS=$(grep '^ODOO_MASTER_PASSWORD=' .env | cut -d= -f2-)
sed -i "s|^db_password *=.*|db_password = $PG_PASS|" odoo.conf.docker
sed -i "s|^admin_passwd *=.*|admin_passwd = $MASTER_PASS|" odoo.conf.docker

$COMPOSE up -d odoo db

if [ -n "$MODULES" ]; then
    if [ "$MODULES" = "all" ]; then
        echo "    Upgrade all modules..."
        $COMPOSE exec -T odoo odoo -u all -d "$DB" --stop-after-init
    else
        echo "    Upgrade $MODULES..."
        $COMPOSE exec -T odoo odoo -u "$MODULES" -d "$DB" --stop-after-init
    fi
    $COMPOSE restart odoo
else
    $COMPOSE restart odoo
fi

echo
echo "=== Update xong ==="
echo "    Backup: $BACKUP_FILE"
echo "    HEAD:   $NEW_SHA"
sleep 5
curl -sI http://127.0.0.1:8069/web/login | head -1 || true
