# VBS Tailor ERP — Custom Addons

Odoo 19 custom modules cho hệ thống ERP cửa hàng may đo VBS.

## Modules

- **vbs_planning** — Lập kế hoạch sản xuất, stage template, planning slot
- **vbs_erp** — Quản lý đơn hàng may đo, pattern, pricing, SLA, fabric stock, contact log (depends on `vbs_planning`)

## Yêu cầu

- Docker + Docker Compose
- Cổng `8069` trống (có thể đổi qua `ODOO_PORT` trong `.env`)

## Chạy local (dev)

```bash
# 1. Tạo file env
cp .env.example .env
# Sửa POSTGRES_PASSWORD / ODOO_MASTER_PASSWORD trước khi deploy production

# 2. Build & start
docker compose up -d --build

# 3. Lần đầu — init database với 2 modules
docker compose exec odoo odoo -i vbs_planning,vbs_erp --stop-after-init

# 4. Start lại service odoo
docker compose restart odoo
```

Truy cập: http://localhost:8069

## Deploy (server)

Dùng script tự động:

```bash
./deploy.sh
```

Script sẽ: cài Docker nếu chưa có → tạo `.env` từ `.env.example` → build & start containers → in link truy cập.

Sau khi chạy xong lần đầu, init DB:

```bash
docker compose exec odoo odoo -i vbs_planning,vbs_erp --stop-after-init
docker compose restart odoo
```

## Các tác vụ thường dùng

```bash
# Xem log
docker compose logs -f odoo

# Update modules sau khi sửa code
docker compose exec odoo odoo -u vbs_erp,vbs_planning --stop-after-init
docker compose restart odoo

# Vào shell Odoo
docker compose exec odoo odoo shell -d VBS_ERP

# Backup DB
docker compose exec db pg_dump -U odoo VBS_ERP > backup_$(date +%F).sql

# Restore DB
cat backup.sql | docker compose exec -T db psql -U odoo VBS_ERP

# Stop toàn bộ
docker compose down

# Stop + xóa data (cẩn thận!)
docker compose down -v
```

## Cấu trúc

```
custom_addons/
├── docker-compose.yml      # Odoo 19 + Postgres 16
├── Dockerfile              # Base odoo:19.0 + copy addons
├── odoo.conf.docker        # Config mount vào container
├── deploy.sh               # Script deploy 1-click
├── .env.example            # Template biến môi trường
├── vbs_planning/           # Module planning (base)
└── vbs_erp/                # Module ERP (depends on vbs_planning)
```

## Biến môi trường (.env)

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `POSTGRES_PASSWORD` | `odoo_secret_2026` | Password DB — **đổi trước khi production** |
| `ODOO_PORT` | `8069` | Port expose ra host |
| `ODOO_MASTER_PASSWORD` | `vbs_admin_2026` | Master password Odoo — **đổi trước khi production** |

## Troubleshooting

- **Port 8069 đã dùng:** đổi `ODOO_PORT` trong `.env` rồi `docker compose up -d`.
- **Module không xuất hiện:** vào *Apps → Update Apps List*, hoặc chạy lệnh update ở trên.
- **Sửa code không thấy đổi:** addons mount `:ro` nên code live-reload, nhưng cần restart odoo hoặc update module để apply model/view changes.
