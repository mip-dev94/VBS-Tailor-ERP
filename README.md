# VBS Tailor ERP — Custom Addons

Odoo 19 custom modules cho hệ thống ERP cửa hàng may đo VBS.

## Modules

- **vbs_base** — Models nền: constants, groups, partner extension, payment record
- **vbs_config** — Cấu hình: pattern (rập), pricing, SLA, settings
- **vbs_contact** — Nhật ký liên hệ khách hàng (manual + auto-log từ state change)
- **vbs_fabric** — Đặt vải (DV01→DV04), kho vải, fabric stock
- **vbs_garment** — Lệnh sản xuất, garment, vận chuyển LCH/LX, wizard huỷ đồ
- **vbs_hr** — HR extension: groups, branch mapping
- **vbs_planning** — Planning slot cho thợ, stage template
- **vbs_product** — Publish đồ mẫu thành sản phẩm B2C (optional)
- **vbs_erp** — Module bridge (legacy, giữ để tương thích)

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

# 3. Lần đầu — init database với toàn bộ modules VBS
docker compose exec odoo odoo -i vbs_base,vbs_config,vbs_contact,vbs_fabric,vbs_garment,vbs_hr,vbs_planning,vbs_product,vbs_erp --stop-after-init

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
docker compose exec odoo odoo -i vbs_base,vbs_config,vbs_contact,vbs_fabric,vbs_garment,vbs_hr,vbs_planning,vbs_product,vbs_erp --stop-after-init
docker compose restart odoo
```

## Các tác vụ thường dùng

```bash
# Xem log
docker compose logs -f odoo

# Update modules sau khi sửa code
docker compose exec odoo odoo -u vbs_base,vbs_config,vbs_contact,vbs_erp,vbs_garment,vbs_hr,vbs_product,vbs_planning --stop-after-init

docker compose restart odoo

# Vào shell Odoo
docker compose exec odoo odoo shell -d VBS_ERP

# Backup DB (định dạng plain SQL) — luôn dùng `-T` để tránh TTY làm hỏng output
docker compose exec -T db pg_dump -U odoo --no-owner --no-privileges VBS_ERP > backup_$(date +%F).sql

# Backup DB (định dạng custom, nén sẵn, restore linh hoạt hơn — khuyến nghị)
docker compose exec -T db pg_dump -U odoo --no-owner --no-privileges -Fc VBS_ERP > backup_$(date +%F).dump

# Backup filestore (attachment / ảnh / tài liệu)
docker compose exec -T odoo tar czf - -C /var/lib/odoo/filestore VBS_ERP > filestore_$(date +%F).tar.gz

# Restore DB — QUAN TRỌNG: phải drop & create DB trống trước, restore vào DB đã có dữ liệu sẽ lỗi COPY state
docker compose stop odoo
docker compose exec -T db psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS \"VBS_ERP\";"
docker compose exec -T db psql -U odoo -d postgres -c "CREATE DATABASE \"VBS_ERP\" OWNER odoo;"

# ... nếu backup là plain SQL:
cat backup_2026-04-18.sql | docker compose exec -T db psql -U odoo -d VBS_ERP

# ... hoặc nếu backup là custom format (-Fc):
cat backup_2026-04-18.dump | docker compose exec -T db pg_restore -U odoo -d VBS_ERP --no-owner --no-privileges

# Restore filestore
cat filestore_2026-04-18.tar.gz | docker compose exec -T odoo tar xzf - -C /var/lib/odoo/filestore

docker compose start odoo

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
├── vbs_base/               # Models nền, constants, groups
├── vbs_config/             # Pattern, pricing, SLA, settings
├── vbs_contact/            # Nhật ký liên hệ khách
├── vbs_fabric/             # Đặt vải + kho vải
├── vbs_garment/            # Lệnh sản xuất + vận chuyển
├── vbs_hr/                 # HR / branch
├── vbs_planning/           # Planning slot
├── vbs_product/            # Publish B2C (optional)
└── vbs_erp/                # Bridge module (legacy)
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
- **Restore lỗi `syntax error at or near "9"` (hoặc số bất kỳ):** DB đích đã tồn tại data → lệnh `CREATE TABLE` báo duplicate → COPY block vỡ, psql đọc data row như SQL. **Fix:** drop & tạo lại DB rỗng rồi restore (xem lệnh ở trên).
- **Backup rỗng / file nhỏ bất thường:** quên `-T` khi `docker compose exec` → TTY chèn ký tự điều khiển. Luôn dùng `docker compose exec -T`.
