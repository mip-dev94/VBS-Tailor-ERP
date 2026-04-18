# -*- coding: utf-8 -*-
"""Helpers dùng chung cho tất cả script import/export.

Import bằng cách paste vào đầu script qua `exec(open(...).read())` hoặc
import trực tiếp nếu đặt trong sys.path. Dùng được cả 2 cách.
"""
import re
from datetime import datetime


# ── MAPPING: Excel → ERP Selection keys ─────────────────────────────────────
# Tình trạng (cột "Tình trạng" trong Excel) → vbs.garment.state
GARMENT_STATE_MAP = {
    'nháp': 'nhap',
    'nhap': 'nhap',
    'lược': 'luoc',
    'luoc': 'luoc',
    'lần 2': 'lan_2',
    'lan 2': 'lan_2',
    'lan_2': 'lan_2',
    'ht': 'hoan_thien',
    'hoàn thiện': 'hoan_thien',
    'hoan thien': 'hoan_thien',
    'hoan_thien': 'hoan_thien',
    'huỷ': 'huy',
    'huy': 'huy',
    'sửa': 'lan_2',   # "Sửa" thường là đồ đang chỉnh, coi như lần 2
    'sua': 'lan_2',
}

# Vị trí (cột "Vị trí" trong Excel) → vbs.garment.location
GARMENT_LOCATION_MAP = {
    'cửa hàng': 'cua_hang',
    'cua hang': 'cua_hang',
    'về xưởng': 've_xuong',
    've xuong': 've_xuong',
    'xưởng': 've_xuong',
    'xuong': 've_xuong',
    'qc': 'qc',
    'văn phòng': 'van_phong',
    'van phong': 'van_phong',
    'đã trả khách': 'da_tra',
    'da tra khach': 'da_tra',
    'đã trả': 'da_tra',
    'da tra': 'da_tra',
    'huỷ đồ': 'huy',
    'huy do': 'huy',
    'huỷ': 'huy',
    'huy': 'huy',
}

# Loại đồ (cột "Loại đồ" Excel) → vbs.garment.garment_type
# ERP lưu từng món riêng; "Bộ comple X mảnh" được map về phần áo. Phần quần/gile
# nếu có thì tạo row riêng (thường 1 row Excel = 1 món đã được sale tách sẵn).
GARMENT_TYPE_MAP = {
    # Sơ mi
    'sơ mi': 'so_mi',
    'so mi': 'so_mi',
    'sơ mi tux': 'so_mi_tux',
    'sơ mi tạo kiểu': 'so_mi_tao_kieu',
    # Quần
    'quần': 'quan',
    'quan': 'quan',
    'quần comple': 'quan_comple',
    'quan comple': 'quan_comple',
    # Áo khoác / Comple
    'áo khoác': 'ao_khoac',       # legacy — map về legacy field
    'ao khoac': 'ao_khoac',
    'áo ngắn sb': 'ao_ngan_sb',
    'áo ngắn pb': 'ao_ngan_pb',
    'áo dài sb': 'ao_dai_sb',
    'áo dài pb': 'ao_dai_pb',
    'áo comple sb': 'ao_comple_sb',
    'áo comple đb': 'ao_comple_db',
    'áo comple db': 'ao_comple_db',
    'bộ comple 2 mảnh': 'ao_comple_sb',  # 2 mảnh = áo + quần → lưu phần áo
    'bo comple 2 manh': 'ao_comple_sb',
    'bộ comple 3 mảnh': 'ao_comple_db',  # 3 mảnh = áo + quần + gile → lưu phần áo
    'bo comple 3 manh': 'ao_comple_db',
    # Gile
    'gile': 'gile',                # legacy
    'áo gile': 'gile',
    'ao gile': 'gile',
    'gile sb': 'gile_sb',
    'gile dd': 'gile_dd',
    # Khác
    'polo': 'polo',
    'budong': 'budong',
    'bomber': 'bomber',
    'chân váy': 'chan_vay',
    'chan vay': 'chan_vay',
}

# Tình trạng liên hệ → vbs.contact.log.tinh_trang
CONTACT_STATUS_MAP = {
    'đã liên hệ': 'da_lien_he',
    'da lien he': 'da_lien_he',
    'chờ liên hệ': 'cho_lien_he',
    'cho lien he': 'cho_lien_he',
}

# Trạng thái phiếu vải (sheet "Theo dõi đặt vải") → vbs.fabric.order.state
FABRIC_STATE_MAP = {
    'chưa về': 'cho_ve',
    'chua ve': 'cho_ve',
    'đã về': 'da_ve',
    'da ve': 'da_ve',
    'chờ duyệt': 'draft',
    'cho duyet': 'draft',
    'chờ đặt': 'cho_dat',
    'cho dat': 'cho_dat',
}


def norm(s):
    """Normalize text: strip, lower, collapse whitespace."""
    if s is None:
        return ''
    return re.sub(r'\s+', ' ', str(s)).strip().lower()


def map_value(value, mapping, default=None, label=''):
    """Map giá trị Excel → key Selection, in cảnh báo nếu không match."""
    n = norm(value)
    if not n:
        return default
    if n in mapping:
        return mapping[n]
    # thử match prefix (ví dụ "Hoàn thiện (ghi chú thêm)" → hoan_thien)
    for k, v in mapping.items():
        if n.startswith(k) or k in n:
            return v
    print(f'  [WARN] {label}: không map được "{value}" → dùng default "{default}"')
    return default


def to_date(value):
    """Convert Excel cell → date. Chấp nhận datetime, string dd/mm/yyyy, hoặc None."""
    if value is None or value == '':
        return False
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        s = value.strip()
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
    return False


def to_datetime(value):
    if value is None or value == '':
        return False
    if isinstance(value, datetime):
        return value
    return False


def find_or_create_partner(env, name, extra=None):
    """Tìm partner theo name (case-insensitive); tạo mới nếu không có.

    Dùng cho sale/CS nhập tay — không validate kỹ, chỉ best-effort match.
    Trả về recordset (1 record) hoặc empty recordset nếu name rỗng.
    """
    Partner = env['res.partner']
    if not name:
        return Partner
    name = str(name).strip()
    if not name:
        return Partner
    p = Partner.search([
        ('name', '=ilike', name),
        ('user_ids', '=', False),
    ], limit=1)
    if p:
        return p
    vals = {'name': name, 'company_type': 'person'}
    if extra:
        vals.update(extra)
    return Partner.create(vals)


def find_order_for_partner(env, partner, create_if_missing=True):
    """Tìm sale.order draft/mới nhất của partner; tạo mới nếu chưa có."""
    SO = env['sale.order']
    if not partner:
        return SO
    order = SO.search([
        ('partner_id', '=', partner.id),
    ], order='id desc', limit=1)
    if order:
        return order
    if not create_if_missing:
        return SO
    return SO.create({
        'partner_id': partner.id,
        'order_type': 'b2b',
    })
