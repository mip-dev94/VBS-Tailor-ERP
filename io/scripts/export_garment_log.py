# -*- coding: utf-8 -*-
"""Export vbs.garment → Excel theo định dạng sheet "Xuất nhập đồ(new)".

Usage:
    docker exec -i custom_addons-odoo-1 odoo shell \
        -c /etc/odoo/odoo.conf -d VBS_ERP --no-http \
        < io/scripts/export_garment_log.py

Filter: chỉnh DOMAIN nếu muốn lọc theo state/partner/date.
"""
import openpyxl
from datetime import datetime, date

OUTPUT_FILE = f'/mnt/io/output/xuat_nhap_do_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
DOMAIN = []   # vd [('state','!=','huy'), ('create_date','>=','2026-01-01')]

Garment = env['vbs.garment']
garments = Garment.search(DOMAIN, order='id')
print(f'Export {len(garments)} garments → {OUTPUT_FILE}')

# Selection labels để export human-readable
state_labels = dict(Garment._fields['state'].selection)
location_labels = dict(Garment._fields['location'].selection)
type_labels = dict(Garment._fields['garment_type'].selection)

wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Xuất nhập đồ(new)'

HEADERS = (
    ['STT', 'Tên khách', 'Loại đồ', 'Chi tiết đồ', 'Tình trạng', 'Vị trí', 'Ngày trả khách']
    + [f'LCH{i}' for i in range(1, 9)]
    + [f'LX{i}' for i in range(1, 9)]
    + ['Mã Sapo', 'Sale xác nhận', 'Đã kiểm tra', 'Lý do huỷ']
)
ws.append(HEADERS)

for idx, g in enumerate(garments, start=1):
    # Tách move thành 8 cặp LCH/LX theo thứ tự
    lch_dates = []
    lx_dates = []
    for m in g.move_ids.sorted('move_date'):
        if m.move_type == 'lch':
            lch_dates.append(m.move_date.date() if m.move_date else None)
        elif m.move_type == 'lx':
            lx_dates.append(m.move_date.date() if m.move_date else None)
    lch_dates = (lch_dates + [None] * 8)[:8]
    lx_dates = (lx_dates + [None] * 8)[:8]

    row = [
        idx,
        g.partner_id.name or '',
        type_labels.get(g.garment_type, g.garment_type or ''),
        g.detail or '',
        state_labels.get(g.state, g.state or ''),
        location_labels.get(g.location, g.location or ''),
        g.date_return or '',
    ] + lch_dates + lx_dates + [
        g.sapo_code or '',
        'x' if g.confirmed_sale else '',
        'x' if g.confirmed_qa else '',
        g.cancel_reason or '',
    ]
    ws.append(row)

# Auto-width cơ bản
for col_cells in ws.columns:
    max_len = max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
    ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 40)

wb.save(OUTPUT_FILE)
print(f'Đã ghi: {OUTPUT_FILE}')
