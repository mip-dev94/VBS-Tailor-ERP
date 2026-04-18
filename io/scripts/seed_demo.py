# -*- coding: utf-8 -*-
"""Seed demo data đầy đủ cho VBS ERP — demo full tất cả module.

Data lấy từ:
 - Nhật ký xuất nhập đồ cửa hàng VBS HN 2026.xlsx
 - 20251130-HaNoi-DV01A.xlsx

Khách hàng anonymized: Khách A, B, C, D, E.
Mỗi module ~10 sample, đủ mọi state/location/pattern.

Usage (trên VM):
    docker compose exec -T odoo odoo shell -d VBS_ERP --no-http \\
        < odoo/custom_addons/io/scripts/seed_demo.py

Idempotent: skip nếu đã tồn tại (dùng marker note 'SEED_DEMO').
"""
from datetime import date, datetime, timedelta

SEED_TAG = '[SEED_DEMO]'


def _seeded(env, model, domain):
    """True nếu đã có record seed (dựa vào SEED_TAG trong note hoặc name)."""
    return bool(env[model].sudo().search_count(domain))


def _log(msg):
    print(f'  >>> {msg}')


# ═══════════════════════════════════════════════════════════════════════════
# 1. res.partner — 5 khách A-E + 3 nhân viên xưởng
# ═══════════════════════════════════════════════════════════════════════════
_log('1/12 — res.partner (5 khách + 3 NV)')
Partner = env['res.partner']

CUSTOMERS_DATA = [
    ('Khách A', 'A. Nguyễn Văn An', '0901000001', 'an@demo.vbs', 'Hà Nội'),
    ('Khách B', 'B. Trần Thị Bình', '0901000002', 'binh@demo.vbs', 'Hà Nội'),
    ('Khách C', 'C. Lê Văn Cường', '0901000003', 'cuong@demo.vbs', 'Hà Nội'),
    ('Khách D', 'D. Phạm Quốc Dũng', '0901000004', 'dung@demo.vbs', 'Hà Nội'),
    ('Khách E', 'E. Hoàng Minh Em', '0901000005', 'em@demo.vbs', 'Hà Nội'),
]
customers = {}
for short, fullname, phone, emailx, city in CUSTOMERS_DATA:
    p = Partner.sudo().search([('name', '=', short)], limit=1)
    if not p:
        p = Partner.sudo().create({
            'name': short,
            'company_type': 'person',
            'phone': phone,
            'email': emailx,
            'city': city,
            'comment': f'{SEED_TAG} {fullname}',
        })
    customers[short] = p

# ═══════════════════════════════════════════════════════════════════════════
# 2. hr.employee — sale, xưởng, QC
# ═══════════════════════════════════════════════════════════════════════════
_log('2/12 — hr.employee (3 NV demo)')
Employee = env['hr.employee']
EMPLOYEES_DATA = [
    ('NV Sale HN', 'Sale'),
    ('NV Xưởng HN', 'Xưởng'),
    ('NV QC HN', 'QC'),
]
employees = {}
for name, job in EMPLOYEES_DATA:
    e = Employee.sudo().search([('name', '=', name)], limit=1)
    if not e:
        e = Employee.sudo().create({
            'name': name,
            'job_title': job,
        })
    employees[name] = e

# ═══════════════════════════════════════════════════════════════════════════
# 3. vbs.fabric.type — 6 loại vải master data
# ═══════════════════════════════════════════════════════════════════════════
_log('3/12 — vbs.fabric.type (6 hãng/mã vải)')
FabricType = env['vbs.fabric.type']
FABRIC_TYPES_DATA = [
    ('DRG-001', 'Drago Navy Plain', 'Drago', 850000, 'Trơn navy, wool 100%'),
    ('DRG-002', 'Drago Grey Check', 'Drago', 920000, 'Kẻ ô nhỏ, grey'),
    ('VBC-001', 'VBC Black SB', 'VBC', 780000, 'Đen trơn, wool blend'),
    ('VBC-002', 'VBC Stripe', 'VBC', 810000, 'Kẻ dọc đen'),
    ('LP-001', 'Loro Piana Blue', 'Loro Piana', 1850000, 'Super 150s'),
    ('HES-001', 'Hesworth Charcoal', 'Hesworth', 720000, 'Charcoal wool'),
]
fabric_types = {}
for code, name, brand, price, note in FABRIC_TYPES_DATA:
    ft = FabricType.sudo().search([('code', '=', code)], limit=1)
    if not ft:
        ft = FabricType.sudo().create({
            'code': code,
            'name': name,
            'fabric_brand': brand,
            'price_per_meter': price,
            'note': note,
        })
    fabric_types[code] = ft

# ═══════════════════════════════════════════════════════════════════════════
# 4. vbs.pricing.product — labor cost cho các loại đồ
# ═══════════════════════════════════════════════════════════════════════════
_log('4/12 — vbs.pricing.product (labor cost)')
Pricing = env['vbs.pricing.product']
PRICING_DATA = [
    ('so_mi', 300000),
    ('ao_comple_sb', 2500000),
    ('ao_comple_db', 2800000),
    ('quan_comple', 800000),
    ('quan', 600000),
    ('gile_sb', 900000),
    ('ao_ngan_sb', 2200000),
    ('ao_dai_sb', 2600000),
    ('polo', 250000),
    ('chan_vay', 500000),
]
for ptype, cost in PRICING_DATA:
    if not Pricing.sudo().search([('product_type', '=', ptype)], limit=1):
        Pricing.sudo().create({
            'product_type': ptype,
            'labor_cost': cost,
            'note': f'{SEED_TAG} demo',
        })

# ═══════════════════════════════════════════════════════════════════════════
# 5. vbs.sla.config — SLA cho vài loại đồ
# ═══════════════════════════════════════════════════════════════════════════
_log('5/12 — vbs.sla.config (SLA time)')
Sla = env['vbs.sla.config']
SLA_DATA = [
    ('so_mi', 'nhap', 3),
    ('so_mi', 'luoc', 5),
    ('so_mi', 'lan_2', 3),
    ('ao_comple_sb', 'nhap', 5),
    ('ao_comple_sb', 'luoc', 10),
    ('ao_comple_sb', 'lan_2', 7),
    ('quan_comple', 'nhap', 3),
    ('quan_comple', 'luoc', 7),
]
for gtype, st, days in SLA_DATA:
    if not Sla.sudo().search([('garment_type', '=', gtype), ('state', '=', st)], limit=1):
        Sla.sudo().create({
            'garment_type': gtype,
            'state': st,
            'max_days': days,
        })

# ═══════════════════════════════════════════════════════════════════════════
# 6. vbs.stage.template — step template cho 3 loại đồ
# ═══════════════════════════════════════════════════════════════════════════
_log('6/12 — vbs.stage.template')
StageTpl = env['vbs.stage.template']
STAGE_DATA = [
    ('so_mi', 10, 'do'),
    ('so_mi', 20, 'cat'),
    ('so_mi', 30, 'may'),
    ('so_mi', 40, 'luoc'),
    ('so_mi', 50, 'kiem_tra'),
    ('so_mi', 60, 'hoan_thien'),
    ('ao_comple_sb', 10, 'do'),
    ('ao_comple_sb', 20, 'cat'),
    ('ao_comple_sb', 30, 'may'),
    ('ao_comple_sb', 40, 'luoc'),
    ('ao_comple_sb', 50, 'sua'),
    ('ao_comple_sb', 60, 'kiem_tra'),
    ('ao_comple_sb', 70, 'hoan_thien'),
    ('quan_comple', 10, 'do'),
    ('quan_comple', 20, 'cat'),
    ('quan_comple', 30, 'may'),
    ('quan_comple', 40, 'hoan_thien'),
]
for gtype, seq, step in STAGE_DATA:
    if not StageTpl.sudo().search([('garment_type', '=', gtype), ('step_type', '=', step)], limit=1):
        StageTpl.sudo().create({
            'garment_type': gtype,
            'sequence': seq,
            'step_type': step,
        })

# ═══════════════════════════════════════════════════════════════════════════
# 7. vbs.pattern — 8 rập (5 custom / 3 template)
# ═══════════════════════════════════════════════════════════════════════════
_log('7/12 — vbs.pattern (8 rập)')
Pattern = env['vbs.pattern']
PATTERN_DATA = [
    # (partner_key, garment_type, pattern_type, storage, meters_std, measurements)
    ('Khách A', 'ao_comple_sb', 'custom', 'Giá 1-A', 3.5, 'Ngực 92 / Eo 82 / Vai 44 / Dài áo 72'),
    ('Khách A', 'quan_comple', 'custom', 'Giá 1-A', 1.3, 'Eo 82 / Hông 96 / Dài quần 102'),
    ('Khách B', 'ao_ngan_sb', 'custom', 'Giá 2-B', 3.2, 'Ngực 96 / Eo 88 / Vai 46'),
    ('Khách C', 'ao_comple_db', 'custom', 'Giá 3-C', 4.0, 'Ngực 100 / Eo 92 / Vai 47 / Dài áo 75'),
    ('Khách D', 'so_mi', 'custom', 'Giá 4-D', 1.8, 'Ngực 94 / Vai 45 / Dài tay 62'),
    (None, 'so_mi', 'template', 'Template-A', 1.8, 'Rập chuẩn sơ mi size M'),
    (None, 'quan_comple', 'template', 'Template-A', 1.3, 'Rập chuẩn quần comple size 32'),
    (None, 'ao_comple_sb', 'template', 'Template-A', 3.5, 'Rập chuẩn comple SB size 48'),
]
patterns = {}
for partner_key, gtype, ptype, storage, meters, meas in PATTERN_DATA:
    partner = customers.get(partner_key) if partner_key else False
    key = f'{partner_key or "TPL"}-{gtype}'
    domain = [('garment_type', '=', gtype), ('pattern_type', '=', ptype)]
    if partner:
        domain.append(('partner_id', '=', partner.id))
    else:
        domain.append(('partner_id', '=', False))
    existing = Pattern.sudo().search(domain, limit=1)
    if existing:
        patterns[key] = existing
        continue
    patterns[key] = Pattern.sudo().create({
        'partner_id': partner.id if partner else False,
        'garment_type': gtype,
        'pattern_type': ptype,
        'storage_location': storage,
        'fabric_meters_std': meters,
        'measurements': meas,
        'note': f'{SEED_TAG} rập demo',
    })

# ═══════════════════════════════════════════════════════════════════════════
# 8. sale.order + vbs.garment — 10 đồ, mọi state/location
# ═══════════════════════════════════════════════════════════════════════════
_log('8/12 — sale.order + vbs.garment (10 đồ)')
SO = env['sale.order']
Garment = env['vbs.garment']
Move = env['vbs.garment.move']

today = fields.Date.today()
now = fields.Datetime.now()

# Mỗi khách 1 đơn B2B riêng (sửa: một số có 2-3 đồ cùng đơn để demo set)
orders = {}
for short, p in customers.items():
    o = SO.sudo().search([
        ('partner_id', '=', p.id),
        ('order_type', '=', 'b2b'),
    ], limit=1)
    if not o:
        o = SO.sudo().create({
            'partner_id': p.id,
            'order_type': 'b2b',
            'note': f'{SEED_TAG} Đơn demo cho {short}',
        })
    orders[short] = o

# 10 đồ với state/location đa dạng, spec chi tiết
GARMENTS_DATA = [
    # (partner, garment_type, state, location, detail, fabric_code, meters, extra_spec)
    ('Khách A', 'ao_comple_sb', 'nhap', 'cua_hang', 'Comple navy SB — anh An đặt cưới',
     'DRG-001', 3.5,
     {'hoa_tiet_vai': 'tron', 'dai_ao': 72.0, 'dai_tay': 62.5,
      'so_hang_cuc': 'mot_hang', 'tui_ao': 'nap', 'lot_ao': 'lot_ca', 'lo_ve': 'co_lv',
      'confirmed_sale': True, 'sapo_code': 'SP-A-001'}),

    ('Khách A', 'quan_comple', 'nhap', 'cua_hang', 'Quần comple navy đi kèm bộ',
     'DRG-001', 1.3,
     {'dai_quan': 102.0, 'confirmed_sale': True, 'sapo_code': 'SP-A-002'}),

    ('Khách B', 'ao_ngan_sb', 'luoc', 've_xuong', 'Áo ngắn SB grey — thử lần 1 OK',
     'DRG-002', 3.2,
     {'hoa_tiet_vai': 'ke_o_vua', 'dai_ao': 68.0, 'dai_tay': 61.0,
      'so_hang_cuc': 'mot_hang', 'tui_ao': 'op', 'lot_ao': 'lot_nua', 'lo_ve': 'khong_lv',
      'confirmed_sale': True, 'sapo_code': 'SP-B-001'}),

    ('Khách C', 'ao_comple_db', 'lan_2', 'qc', 'Comple DB đen — sửa rộng eo 2cm',
     'VBC-001', 4.0,
     {'hoa_tiet_vai': 'tron', 'dai_ao': 75.0, 'dai_tay': 63.0,
      'so_hang_cuc': 'hai_hang', 'tui_ao': 'nap', 'lot_ao': 'lot_ca', 'lo_ve': 'co_lv',
      'confirmed_sale': True, 'confirmed_qa': False, 'sapo_code': 'SP-C-001'}),

    ('Khách C', 'gile_sb', 'lan_2', 'qc', 'Gile SB đen kèm bộ comple DB',
     'VBC-001', 0.8,
     {'so_hang_cuc': 'mot_hang', 'confirmed_sale': True, 'sapo_code': 'SP-C-002'}),

    ('Khách D', 'so_mi', 'hoan_thien', 'van_phong', 'Sơ mi trắng — khách đã thử OK',
     'VBC-002', 1.8,
     {'hoa_tiet_vai': 'ke_doc', 'dai_ao': 74.0, 'dai_tay': 62.0,
      'confirmed_sale': True, 'confirmed_qa': True, 'sapo_code': 'SP-D-001'}),

    ('Khách D', 'so_mi_tux', 'hoan_thien', 'da_tra', 'Sơ mi tux trắng — đã trả khách',
     'VBC-002', 1.8,
     {'hoa_tiet_vai': 'tron', 'dai_ao': 74.0,
      'confirmed_sale': True, 'confirmed_qa': True,
      'sapo_code': 'SP-D-002',
      'date_return': today - timedelta(days=3)}),

    ('Khách E', 'ao_comple_sb', 'hoan_thien', 'da_tra', 'Comple SB Loro Piana — high-end, đã trả',
     'LP-001', 3.6,
     {'hoa_tiet_vai': 'tron', 'dai_ao': 71.0, 'dai_tay': 62.0,
      'so_hang_cuc': 'mot_hang', 'tui_ao': 'nap', 'lot_ao': 'lot_ca', 'lo_ve': 'co_lv',
      'confirmed_sale': True, 'confirmed_qa': True,
      'sapo_code': 'SP-E-001',
      'date_return': today - timedelta(days=10)}),

    ('Khách E', 'quan', 'nhap', 'cua_hang', 'Quần lẻ charcoal — đang đo lại',
     'HES-001', 1.2,
     {'dai_quan': 100.0, 'sapo_code': 'SP-E-002'}),

    ('Khách B', 'chan_vay', 'huy', 'huy', 'Chân váy — khách huỷ đổi ý',
     'VBC-001', 1.5,
     {'cancel_reason': 'Khách đổi ý, chuyển sang mua sẵn',
      'date_cancelled': now - timedelta(days=2)}),
]

garments = []
for idx, (partner_key, gtype, state, location, detail, fcode, meters, extra) in enumerate(GARMENTS_DATA):
    partner = customers[partner_key]
    order = orders[partner_key]
    # Check existing by sapo_code (unique-ish marker)
    sapo = extra.get('sapo_code')
    if sapo:
        existing = Garment.sudo().search([('sapo_code', '=', sapo)], limit=1)
        if existing:
            garments.append(existing)
            continue
    vals = {
        'order_id': order.id,
        'garment_type': gtype,
        'detail': detail,
        'fabric_id': fabric_types[fcode].id,
        'fabric_meters': meters,
        'date_entry': today - timedelta(days=30 - idx * 2),
        'planned_date': today + timedelta(days=7 - idx),
        'note': f'{SEED_TAG} đồ demo',
    }
    # Link pattern nếu có match custom cho partner+gtype
    pkey = f'{partner_key}-{gtype}'
    if pkey in patterns:
        vals['pattern_id'] = patterns[pkey].id
    vals.update(extra)
    # Set state cuối cùng — vì có constraint lan_2→hoan_thien cần confirmed_qa
    target_state = vals.pop('state', state)
    target_location = vals.pop('location', location)
    g = Garment.sudo().create(vals)
    # Move state/location riêng (sau khi create để tránh constraint kẹt)
    write_vals = {}
    if target_state and g.state != target_state:
        # nếu target là huy, bảo đảm có cancel_reason
        if target_state == 'huy' and not g.cancel_reason:
            write_vals['cancel_reason'] = extra.get('cancel_reason', 'Huỷ demo')
        write_vals['state'] = target_state
    if target_location and g.location != target_location:
        write_vals['location'] = target_location
    if write_vals:
        g.sudo().write(write_vals)
    garments.append(g)

# ═══════════════════════════════════════════════════════════════════════════
# 9. vbs.garment.move — history LCH/LX cho các đồ đã ở xưởng/QC/trả
# ═══════════════════════════════════════════════════════════════════════════
_log('9/12 — vbs.garment.move (history LCH/LX)')
# Tạo lịch sử đi-về thực tế cho 5 đồ tiêu biểu
move_plans = {
    1: [('lch', -14), ('lx', -7)],  # Khách B áo ngắn — 2 lần
    2: [('lch', -20), ('lx', -14), ('lch', -10), ('lx', -5)],  # Khách C comple — 4 lần
    3: [('lch', -18), ('lx', -12), ('lch', -8)],  # Khách C gile — 3 lần
    4: [('lch', -25), ('lx', -18), ('lch', -10), ('lx', -4)],  # Khách D sơ mi — 4 lần
    5: [('lch', -28), ('lx', -20), ('lch', -15), ('lx', -11)],  # Khách D tux — 4 lần
    6: [('lch', -35), ('lx', -25), ('lch', -18), ('lx', -12)],  # Khách E comple — 4 lần
}
for garment_idx, moves in move_plans.items():
    if garment_idx >= len(garments):
        continue
    g = garments[garment_idx]
    if g.move_ids:
        continue  # đã có history
    for move_type, days_offset in moves:
        Move.sudo().create({
            'garment_id': g.id,
            'move_type': move_type,
            'move_date': now + timedelta(days=days_offset),
            'note': f'{SEED_TAG} move demo',
        })

# ═══════════════════════════════════════════════════════════════════════════
# 10. vbs.fabric.order (DV01A) — 5 đơn ở 4 state (DV01/DV02/DV03/DV04)
# ═══════════════════════════════════════════════════════════════════════════
_log('10/12 — vbs.fabric.order + lines (5 phiếu DV01-DV04)')
FabricOrder = env['vbs.fabric.order']
FabricLine = env['vbs.fabric.order.line']
FabricStock = env['vbs.fabric.stock']

# Phiếu 1 — DV01 (draft, chưa duyệt)
# Phiếu 2 — DV02 (đã duyệt, chưa đặt xong)
# Phiếu 3 — DV03 (đã đặt, chưa về)
# Phiếu 4 — DV04 (vải đã về)
# Phiếu 5 — DV04 cũ (vải đã về 10 ngày trước)

FABRIC_ORDER_PLANS = [
    # (days_offset_order, target_state, lines_spec)
    (-2, 'draft', [
        ('Khách A', 'DRG-001', 4.0, 'ao_comple_sb', 'tron', 'Comple cưới',
         {'dai_ao': '72', 'dai_tay_ao': '62', 'button_row': 'mot_hang',
          'pocket': 'nap', 'lining': 'lot_ca', 'cuff': 'co_lv', 'sapo_code': 'SP-A-001'}),
        ('Khách A', 'DRG-001', 1.3, 'quan_comple', 'tron', 'Quần kèm bộ',
         {'dai_quan': '102', 'sapo_code': 'SP-A-002'}),
    ]),
    (-5, 'cho_dat', [
        ('Khách B', 'DRG-002', 3.2, 'ao_khoac_le', 'ke_o_vua', 'Áo ngắn SB grey',
         {'dai_ao': '68', 'dai_tay_ao': '61', 'button_row': 'mot_hang',
          'pocket': 'op', 'lining': 'lot_nua', 'cuff': 'khong_lv', 'sapo_code': 'SP-B-001'}),
    ]),
    (-12, 'cho_ve', [
        ('Khách C', 'VBC-001', 4.0, 'bo_comple_3', 'tron', 'Comple DB đen 3 mảnh',
         {'dai_ao': '75', 'dai_tay_ao': '63', 'button_row': 'hai_hang',
          'pocket': 'nap', 'lining': 'lot_ca', 'cuff': 'co_lv', 'sapo_code': 'SP-C-001'}),
        ('Khách C', 'VBC-001', 0.8, 'gile', 'tron', 'Gile kèm',
         {'button_row': 'mot_hang', 'sapo_code': 'SP-C-002'}),
    ]),
    (-18, 'da_ve', [
        ('Khách D', 'VBC-002', 1.8, 'so_mi', 'ke_doc', 'Sơ mi trắng kẻ dọc',
         {'dai_ao': '74', 'dai_tay_ao': '62', 'sapo_code': 'SP-D-001'}),
        ('Khách D', 'VBC-002', 1.8, 'so_mi', 'tron', 'Sơ mi tux trắng',
         {'dai_ao': '74', 'sapo_code': 'SP-D-002'}),
    ]),
    (-25, 'da_ve', [
        ('Khách E', 'LP-001', 3.6, 'bo_comple_2', 'tron', 'Comple SB Loro Piana cao cấp',
         {'dai_ao': '71', 'dai_tay_ao': '62', 'button_row': 'mot_hang',
          'pocket': 'nap', 'lining': 'lot_ca', 'cuff': 'co_lv', 'sapo_code': 'SP-E-001'}),
        ('Khách E', 'HES-001', 1.2, 'quan_le', 'tron', 'Quần lẻ charcoal',
         {'dai_quan': '100', 'sapo_code': 'SP-E-002'}),
    ]),
]

fabric_orders = []
for days_offset, target_state, lines_spec in FABRIC_ORDER_PLANS:
    order_date = today + timedelta(days=days_offset)
    # Idempotency: check by (date_order, first sapo_code)
    first_sapo = lines_spec[0][6].get('sapo_code') if lines_spec else None
    existing = False
    if first_sapo:
        existing_line = FabricLine.sudo().search([
            ('sapo_code', '=', first_sapo),
            ('order_id.note', 'like', SEED_TAG),
        ], limit=1)
        if existing_line:
            existing = existing_line.order_id
    if existing:
        fabric_orders.append(existing)
        continue
    order = FabricOrder.sudo().create({
        'date_order': order_date,
        'note': f'{SEED_TAG} Phiếu demo — state đích {target_state}',
    })
    for partner_key, fcode, qty, gdesc, pattern, gnote, extra in lines_spec:
        partner = customers[partner_key]
        ft = fabric_types[fcode]
        line_vals = {
            'order_id': order.id,
            'partner_id': partner.id,
            'fabric_type_id': ft.id,
            'fabric_brand': ft.fabric_brand,
            'fabric_code': ft.code,
            'garment_desc': gdesc,
            'pattern': pattern,
            'quantity': qty,
            'note': gnote,
        }
        line_vals.update(extra)
        FabricLine.sudo().create(line_vals)
    # Chuyển state theo workflow
    if target_state in ('cho_dat', 'cho_ve', 'da_ve'):
        order.action_approve()
    if target_state in ('cho_ve', 'da_ve'):
        order.action_confirm_ordered()
    if target_state == 'da_ve':
        order.action_mark_arrived()
        # Backdate date_arrived
        order.sudo().write({'date_arrived': order_date + timedelta(days=7)})
    fabric_orders.append(order)

# Link garment ↔ fabric_line theo sapo_code (để demo quan hệ)
for g in garments:
    if g.sapo_code and not g.fabric_line_id:
        line = FabricLine.sudo().search([('sapo_code', '=', g.sapo_code)], limit=1)
        if line:
            g.sudo().write({
                'fabric_line_id': line.id,
                'fabric_order_id': line.order_id.id,
            })

# ═══════════════════════════════════════════════════════════════════════════
# 11. vbs.fabric.stock — tồn kho cho đơn DV04
# ═══════════════════════════════════════════════════════════════════════════
_log('11/12 — vbs.fabric.stock (tồn kho DV04)')
for order in fabric_orders:
    if order.state != 'da_ve':
        continue
    for line in order.line_ids:
        existing = FabricStock.sudo().search([
            ('partner_id', '=', line.partner_id.id),
            ('fabric_type_id', '=', line.fabric_type_id.id if line.fabric_type_id else False),
            ('fabric_order_id', '=', order.id),
        ], limit=1)
        if existing:
            continue
        FabricStock.sudo().create({
            'partner_id': line.partner_id.id,
            'fabric_type_id': line.fabric_type_id.id if line.fabric_type_id else False,
            'fabric_order_id': order.id,
            'fabric_brand': line.fabric_brand or '',
            'fabric_type': (line.fabric_type_id.name if line.fabric_type_id else line.fabric_code or 'Vải'),
            'quantity_received': line.quantity,
            'note': f'{SEED_TAG} stock từ {order.name}',
        })

# ═══════════════════════════════════════════════════════════════════════════
# 12. vbs.contact.log — 10 log thủ công sale ghi
# ═══════════════════════════════════════════════════════════════════════════
_log('12/12 — vbs.contact.log (10 log sale)')
ContactLog = env['vbs.contact.log']

# Disable auto contact log tạm thời khi seed để tránh nhiễu
ICP = env['ir.config_parameter'].sudo()
prev = ICP.get_param('vbs.auto_contact_log', 'True')
# (không tắt — giữ auto log, chỉ thêm manual log)

CONTACT_LOG_DATA = [
    # (partner, garment_idx_or_None, days_offset, noi_dung, ket_qua, tinh_trang)
    ('Khách A', 0, -5, 'Gọi khách hẹn thử đồ lần 1', 'Khách hẹn thứ 7', 'da_lien_he'),
    ('Khách A', 1, -3, 'Nhắn SMS báo tiến độ quần comple', 'Đã nhắn', 'da_lien_he'),
    ('Khách B', 2, -10, 'Khách phản hồi áo rộng vai 1cm', 'Cần sửa', 'da_lien_he'),
    ('Khách B', 2, -2, 'Hẹn khách đến thử lại sau khi sửa', None, 'cho_lien_he'),
    ('Khách C', 3, -8, 'Báo khách vải DV03 đã đặt', 'Khách OK chờ vải về', 'da_lien_he'),
    ('Khách C', 4, -1, 'Gọi báo gile cũng đã cắt xong', None, 'cho_lien_he'),
    ('Khách D', 5, -4, 'Khách đến thử sơ mi — OK', 'Không cần sửa', 'da_lien_he'),
    ('Khách D', 6, -15, 'Báo khách tux đã giao', 'Khách hài lòng', 'da_lien_he'),
    ('Khách E', 7, -20, 'Gửi bộ comple LP cao cấp — follow up feedback', 'Khách đánh giá 5 sao', 'da_lien_he'),
    ('Khách E', 8, 0, 'Hẹn khách đo lại quần charcoal', None, 'cho_lien_he'),
]
for partner_key, garment_idx, days_offset, noi_dung, ket_qua, tinh_trang in CONTACT_LOG_DATA:
    partner = customers[partner_key]
    g_id = garments[garment_idx].id if garment_idx is not None and garment_idx < len(garments) else False
    # Idempotency — skip if có log cùng partner + noi_dung
    existing = ContactLog.sudo().search([
        ('partner_id', '=', partner.id),
        ('noi_dung', '=', noi_dung),
    ], limit=1)
    if existing:
        continue
    ContactLog.sudo().create({
        'date_contact': today + timedelta(days=days_offset),
        'partner_id': partner.id,
        'garment_id': g_id,
        'noi_dung': noi_dung,
        'ket_qua': ket_qua or False,
        'tinh_trang': tinh_trang,
        'note': f'{SEED_TAG} log thủ công demo',
    })

# ═══════════════════════════════════════════════════════════════════════════
# 13. vbs.payment.record — thanh toán 1 phần / toàn bộ cho vài đơn
# ═══════════════════════════════════════════════════════════════════════════
_log('13/12 — vbs.payment.record (thanh toán)')
Payment = env['vbs.payment.record']

# Tính tổng cho các order có garment hoàn thiện để tạo payment
# (sale.order không có amount_total từ order_line vì B2B dùng garment — ta set thủ công qua payment)
PAYMENT_DATA = [
    ('Khách A', -5, 5000000, 'transfer', 'Đặt cọc comple + quần'),
    ('Khách B', -10, 3000000, 'cash', 'Đặt cọc 50%'),
    ('Khách C', -12, 10000000, 'transfer', 'Thanh toán 50% comple DB + gile'),
    ('Khách D', -15, 2500000, 'cash', 'Đủ sơ mi + tux'),
    ('Khách E', -25, 15000000, 'transfer', 'Đủ comple LP cao cấp'),
    ('Khách E', -3, 1500000, 'cash', 'Đặt cọc quần charcoal'),
]
for partner_key, days_offset, amount, method, note in PAYMENT_DATA:
    order = orders[partner_key]
    existing = Payment.sudo().search([
        ('order_id', '=', order.id),
        ('amount', '=', amount),
        ('note', '=', note),
    ], limit=1)
    if existing:
        continue
    Payment.sudo().create({
        'order_id': order.id,
        'date': today + timedelta(days=days_offset),
        'amount': amount,
        'method': method,
        'note': f'{SEED_TAG} {note}',
    })

# ═══════════════════════════════════════════════════════════════════════════
# 14. planning.slot — lịch sản xuất cho 3 đồ đang ở xưởng/QC
# ═══════════════════════════════════════════════════════════════════════════
_log('14/12 — planning.slot (lịch sản xuất)')
Slot = env['planning.slot']
xuong_emp = employees['NV Xưởng HN']
qc_emp = employees['NV QC HN']

SLOT_PLANS = [
    # (garment_idx, employee, days_offset, note)
    (2, xuong_emp, -7, 'Lược áo ngắn Khách B'),
    (3, xuong_emp, -5, 'Sửa comple DB Khách C'),
    (3, qc_emp, -2, 'QC bộ comple Khách C'),
    (4, xuong_emp, -6, 'May gile Khách C'),
    (5, qc_emp, -3, 'QC sơ mi Khách D'),
    (8, xuong_emp, 1, 'Đo quần charcoal Khách E'),
]
for g_idx, emp, days_offset, note in SLOT_PLANS:
    if g_idx >= len(garments):
        continue
    g = garments[g_idx]
    start = datetime.combine(today + timedelta(days=days_offset), datetime.min.time()).replace(hour=1)
    end = start + timedelta(hours=8)
    existing = Slot.sudo().search([
        ('employee_id', '=', emp.id),
        ('garment_id', '=', g.id),
        ('start_datetime', '=', start),
    ], limit=1)
    if existing:
        continue
    Slot.sudo().create({
        'employee_id': emp.id,
        'garment_id': g.id,
        'start_datetime': start,
        'end_datetime': end,
        'state': 'confirmed' if days_offset < 0 else 'draft',
        'note': f'<p>{SEED_TAG} {note}</p>',
    })

# ═══════════════════════════════════════════════════════════════════════════
# Commit
# ═══════════════════════════════════════════════════════════════════════════
env.cr.commit()

print()
print('=' * 60)
print('✅ SEED DEMO HOÀN TẤT')
print('=' * 60)
print(f'  Khách hàng     : {len(customers)} (Khách A..E)')
print(f'  Nhân viên      : {len(employees)}')
print(f'  Loại vải       : {len(fabric_types)}')
print(f'  Rập            : {len(patterns)}')
print(f'  Đơn hàng       : {len(orders)}')
print(f'  Đồ may         : {len(garments)}')
print(f'  Phiếu đặt vải  : {len(fabric_orders)}')
print(f'  Contact log    : ~{len(CONTACT_LOG_DATA)}')
print(f'  Payment        : ~{len(PAYMENT_DATA)}')
print(f'  Planning slot  : ~{len(SLOT_PLANS)}')
print()
print('Vào web UI (https://vbstailor-erp.online) để demo.')
