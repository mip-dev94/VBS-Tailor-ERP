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
# odoo.conf.docker bị sed -i sửa ở bước 5 → reset để git pull không bị conflict
git checkout -- odoo.conf.docker 2>/dev/null || true
git pull --ff-only
NEW_SHA=$(git rev-parse HEAD)
if [ "$OLD_SHA" = "$NEW_SHA" ] && [ "${1:-}" != "all" ]; then
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
    # `|| true` sau grep: nếu không có dòng vbs_* nào → exit 0 thay vì 1 (tránh pipefail).
    CHANGED=$(git diff --name-only "$OLD_SHA" "$NEW_SHA" \
        | { grep -E '^vbs_[a-z_]+/' || true; } \
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

$COMPOSE up -d db
echo "    Chờ DB healthy..."
$COMPOSE exec -T db pg_isready -U odoo -d "$DB" || sleep 5

# Force-update currency symbols — chạy mọi lần deploy, idempotent
$COMPOSE exec -T db psql -U odoo "$DB" -c "
    UPDATE res_currency SET symbol = 'VNĐ' WHERE name = 'VND';
    UPDATE res_currency SET symbol = 'USD' WHERE name = 'USD';
" 2>&1 || true

if [ -n "$MODULES" ]; then
    # Patch schema trước khi start Odoo — tránh crash khi có stored field mới
    # mà column chưa tồn tại trong DB (chicken-and-egg). IF NOT EXISTS = idempotent.
    echo "    Patch schema (new stored fields)..."
    $COMPOSE exec -T db psql -U odoo "$DB" -c "
        ALTER TABLE vbs_fabric_order_line ADD COLUMN IF NOT EXISTS arrived boolean DEFAULT false;
        ALTER TABLE vbs_fabric_order_line ADD COLUMN IF NOT EXISTS date_arrived date;
        ALTER TABLE vbs_fabric_order     ADD COLUMN IF NOT EXISTS arrived_line_count integer DEFAULT 0;
        ALTER TABLE vbs_fabric_order     ADD COLUMN IF NOT EXISTS pending_line_count integer DEFAULT 0;
        ALTER TABLE vbs_product ADD COLUMN IF NOT EXISTS sku character varying;
        ALTER TABLE vbs_product ADD COLUMN IF NOT EXISTS weight_grams integer DEFAULT 0;
        ALTER TABLE vbs_product ADD COLUMN IF NOT EXISTS cost_fabric numeric DEFAULT 0;
        ALTER TABLE vbs_product ADD COLUMN IF NOT EXISTS cost_labor numeric DEFAULT 0;
        ALTER TABLE vbs_product ADD COLUMN IF NOT EXISTS cost_other numeric DEFAULT 0;
        ALTER TABLE vbs_product ADD COLUMN IF NOT EXISTS profit_amount numeric DEFAULT 0;
        ALTER TABLE vbs_product ADD COLUMN IF NOT EXISTS profit_margin_pct numeric DEFAULT 0;
        ALTER TABLE sale_order ADD COLUMN IF NOT EXISTS sale_confirmed boolean DEFAULT false;
        ALTER TABLE sale_order ADD COLUMN IF NOT EXISTS accountant_confirmed boolean DEFAULT false;
        ALTER TABLE sale_order ADD COLUMN IF NOT EXISTS amount_remaining numeric DEFAULT 0;
        ALTER TABLE vbs_fabric_order ADD COLUMN IF NOT EXISTS sale_order_id integer;
        ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS fabric_type_id integer;
        ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS garment_category character varying;
        ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS vbs_product_id integer;
        ALTER TABLE vbs_product ADD COLUMN IF NOT EXISTS garment_category character varying;
        ALTER TABLE vbs_pricing_product ADD COLUMN IF NOT EXISTS garment_type character varying;
        ALTER TABLE vbs_pricing_product ADD COLUMN IF NOT EXISTS set_type character varying DEFAULT 'le';
        ALTER TABLE vbs_pricing_product ADD COLUMN IF NOT EXISTS fabric_type_id integer;
        UPDATE vbs_pricing_product SET garment_type = product_type WHERE garment_type IS NULL AND product_type IS NOT NULL;
        UPDATE vbs_pricing_product SET set_type = 'le' WHERE set_type IS NULL;
        ALTER TABLE vbs_pricing_product DROP CONSTRAINT IF EXISTS vbs_pricing_product_unique_product_type;
        ALTER TABLE vbs_product ADD COLUMN IF NOT EXISTS product_type character varying DEFAULT 'b2c';
        CREATE TABLE IF NOT EXISTS vbs_expense_record (
            id serial PRIMARY KEY,
            name character varying NOT NULL,
            date date,
            amount numeric DEFAULT 0,
            currency_id integer,
            category character varying DEFAULT 'khac',
            note text,
            active boolean DEFAULT true,
            create_date timestamp without time zone,
            write_date timestamp without time zone,
            create_uid integer,
            write_uid integer
        );
    " 2>&1 || true
fi

$COMPOSE up -d odoo db

# Build danh sách modules cần xử lý: git-detected + always-check (nếu chưa installed)
# Dùng psql trực tiếp vào DB (không qua Odoo) nên không bị ảnh hưởng bởi Odoo crash
ALWAYS_CHECK="vbs_product,vbs_crm,vbs_accounting"
INSTALL_MODS=""
UPGRADE_MODS=""

check_and_classify() {
    local mod="$1"
    local cnt
    cnt=$($COMPOSE exec -T db psql -U odoo "$DB" -tAc \
        "SELECT COUNT(*) FROM ir_module_module WHERE name='$mod' AND state='installed';" \
        2>/dev/null | tr -d '[:space:]')
    if [ "${cnt:-0}" = "0" ] || [ -z "$cnt" ]; then
        INSTALL_MODS="${INSTALL_MODS:+$INSTALL_MODS,}$mod"
        echo "    → Install mới: $mod"
    else
        UPGRADE_MODS="${UPGRADE_MODS:+$UPGRADE_MODS,}$mod"
        echo "    → Upgrade: $mod"
    fi
}

# Always-check: đảm bảo các module này luôn được install nếu chưa có
echo "    Kiểm tra module mới..."
IFS=',' read -ra AC_LIST <<< "$ALWAYS_CHECK"
for mod in "${AC_LIST[@]}"; do
    check_and_classify "$mod"
done

# Git-detected modules (không trùng với ALWAYS_CHECK)
if [ -n "$MODULES" ] && [ "$MODULES" != "all" ]; then
    IFS=',' read -ra MOD_LIST <<< "$MODULES"
    for mod in "${MOD_LIST[@]}"; do
        # Bỏ qua nếu đã có trong danh sách rồi
        if echo "$ALWAYS_CHECK" | grep -qw "$mod"; then continue; fi
        check_and_classify "$mod"
    done
fi

# Chạy Odoo 1 lần duy nhất với tất cả args
if [ "${MODULES}" = "all" ]; then
    echo "    Upgrade all modules..."
    $COMPOSE exec -T odoo odoo -u all -d "$DB" --stop-after-init \
        --logfile=/dev/stdout --log-level=warn
elif [ -n "$INSTALL_MODS" ] || [ -n "$UPGRADE_MODS" ]; then
    ODOO_ARGS=""
    [ -n "$INSTALL_MODS" ] && ODOO_ARGS="$ODOO_ARGS -i $INSTALL_MODS"
    [ -n "$UPGRADE_MODS" ] && ODOO_ARGS="$ODOO_ARGS -u $UPGRADE_MODS"
    $COMPOSE exec -T odoo odoo $ODOO_ARGS -d "$DB" --stop-after-init \
        --logfile=/dev/stdout --log-level=warn
fi
$COMPOSE restart odoo

echo
echo "=== Update xong ==="
echo "    Backup: $BACKUP_FILE"
echo "    HEAD:   $NEW_SHA"
sleep 5
curl -sI http://127.0.0.1:8069/web/login | head -1 || true
