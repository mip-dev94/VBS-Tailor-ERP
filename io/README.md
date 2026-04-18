# VBS ERP — Import / Export Excel

Thư mục chứa scripts import Excel → ERP và export ERP → Excel. Mount vào
container Odoo ở `/mnt/io` (xem `docker-compose.yml`).

## Cấu trúc

```
io/
├── input/            # đặt file Excel cần import vào đây
│   ├── nhat_ky.xlsx          # Nhật ký xuất nhập đồ VBS HN
│   └── dv01a.xlsx            # File DV01A (đơn đặt vải)
├── output/           # file Excel được export ra
├── scripts/
│   ├── _lib.py                 # Helpers: mapping Excel ↔ ERP, partner lookup
│   ├── import_garment_log.py   # Sheet "Xuất nhập đồ(new)" → vbs.garment
│   ├── import_contact_log.py   # Sheet "Liên hệ khách hàng" → vbs.contact.log
│   ├── import_fabric_tracker.py# Sheet "Theo dõi đặt vải" → vbs.fabric.order
│   ├── import_dv01a.py         # 1 file DV01A → 1 vbs.fabric.order
│   └── export_garment_log.py   # vbs.garment → Excel
└── README.md
```

## Chạy import

Đặt file Excel vào `io/input/` rồi chạy:

```bash
cd /home/mink/Outsource/ERP_Fashion/odoo/custom_addons

# 1. Garment log (sheet Xuất nhập đồ)
docker exec -i custom_addons-odoo-1 odoo shell \
    -c /etc/odoo/odoo.conf -d VBS_ERP --no-http \
    < io/scripts/import_garment_log.py

# 2. Contact log (sheet Liên hệ khách hàng)
docker exec -i custom_addons-odoo-1 odoo shell \
    -c /etc/odoo/odoo.conf -d VBS_ERP --no-http \
    < io/scripts/import_contact_log.py

# 3. Fabric tracker (sheet Theo dõi đặt vải)
docker exec -i custom_addons-odoo-1 odoo shell \
    -c /etc/odoo/odoo.conf -d VBS_ERP --no-http \
    < io/scripts/import_fabric_tracker.py

# 4. DV01A (1 file = 1 phiếu)
docker exec -i custom_addons-odoo-1 odoo shell \
    -c /etc/odoo/odoo.conf -d VBS_ERP --no-http \
    < io/scripts/import_dv01a.py
```

## Chạy export

```bash
docker exec -i custom_addons-odoo-1 odoo shell \
    -c /etc/odoo/odoo.conf -d VBS_ERP --no-http \
    < io/scripts/export_garment_log.py
```

File xuất ra sẽ nằm trong `io/output/` (có timestamp).

## Workflow đề xuất

1. **Dry-run trước**: mở script, đổi `DRY_RUN = False` → `True`, chạy để xem
   số record sẽ được tạo/cập nhật. Nếu OK, đổi về `False` và chạy lại để
   commit vào DB.
2. **Import theo thứ tự**:
   - Nhập **khách hàng** (tự động qua `find_or_create_partner` — không cần
     bước riêng).
   - Nhập **garment log** (tạo sale.order + partner + garment).
   - Nhập **fabric tracker** (đặt vải có sẵn).
   - Nhập **contact log** (liên hệ khách).
   - Import các file **DV01A** từng cái một (mỗi file = 1 phiếu).
3. **Kiểm tra** trên Odoo UI: mở menu VBS → Đồ may / Đặt vải / Liên hệ, xác
   nhận số lượng record và filter theo trạng thái.
4. **Export** định kỳ (hàng tuần/tháng) để archive hoặc share với stakeholder
   không truy cập ERP.

## Idempotency

Mỗi script có lookup key riêng để tránh duplicate khi re-run:

| Script                    | Lookup key                                |
|---------------------------|-------------------------------------------|
| import_garment_log.py     | (partner_id, garment_type, detail)        |
| import_contact_log.py     | (date_contact, partner_id, noi_dung)      |
| import_fabric_tracker.py  | (line.sapo_code, line.partner_id)         |
| import_dv01a.py           | Không idempotent — mỗi lần = 1 phiếu mới  |

Nếu record đã tồn tại → garment_log sẽ **update**, còn contact_log / fabric_tracker
sẽ **skip**. `import_dv01a.py` luôn tạo phiếu mới (mỗi lần import = 1 DV01
mới), vì 1 file Excel = 1 phiếu thật sự.

## Mapping tuỳ chỉnh

Mở `scripts/_lib.py` để chỉnh mapping giữa giá trị Excel và Selection keys
trong ERP:

- `GARMENT_STATE_MAP` — Tình trạng: Nháp/Lược/Lần 2/HT/Huỷ
- `GARMENT_LOCATION_MAP` — Vị trí: Cửa hàng/Xưởng/QC/Văn phòng/Đã trả/Huỷ
- `GARMENT_TYPE_MAP` — Loại đồ: Sơ mi, Quần, Comple SB/DB, Gile, ...
- `CONTACT_STATUS_MAP` — Tình trạng liên hệ
- `FABRIC_STATE_MAP` — Trạng thái phiếu vải

Nếu Excel có giá trị mới chưa được map, script sẽ in cảnh báo và dùng giá trị
default. Thêm entry mới vào mapping rồi chạy lại.

## Troubleshooting

- **"FileNotFoundError: /mnt/io/input/xxx.xlsx"**: Chưa copy file vào `io/input/`.
  Đặt file `.xlsx` vào đúng thư mục.
- **"KeyError: 'vbs.product'"** hoặc tương tự: module `vbs_product` /
  `vbs_erp` đã uninstalled. Không ảnh hưởng tới script, cứ chạy tiếp.
- **Cảnh báo "[WARN] garment_type: không map được"**: giá trị Excel không
  khớp mapping trong `_lib.py`. Bổ sung entry mới vào `GARMENT_TYPE_MAP`.
- **Import chậm với file lớn (>1000 rows)**: mỗi row tạo sale.order riêng có
  thể tốn vài phút. Nếu quá chậm, có thể tạm tắt `auto_contact_log` bằng
  `env['ir.config_parameter'].set_param('vbs.auto_contact_log', 'False')`
  trước khi import, bật lại sau.
