# -*- coding: utf-8 -*-
"""
Shared selection lists used across all VBS modules.
Import from here to avoid circular dependencies between modules.
"""

GARMENT_TYPE = [
    # ── Áo khoác / Comple ─────────────────────────
    ('ao_ngan_sb', 'Áo ngắn SB'),
    ('ao_ngan_pb', 'Áo ngắn PB'),
    ('ao_dai_sb', 'Áo dài SB'),
    ('ao_dai_pb', 'Áo dài PB'),
    ('ao_comple_sb', 'Áo Comple SB'),
    ('ao_comple_db', 'Áo Comple ĐB'),
    # ── Quần ──────────────────────────────────────
    ('quan_comple', 'Quần Comple'),
    ('quan', 'Quần'),
    # ── Sơ mi ─────────────────────────────────────
    ('so_mi', 'Sơ mi'),
    ('so_mi_tux', 'Sơ mi Tux'),
    ('so_mi_tao_kieu', 'Sơ mi tao kiểu'),
    # ── Gile ──────────────────────────────────────
    ('gile_sb', 'Gile SB'),
    ('gile_dd', 'Gile DD'),
    # ── Khác ──────────────────────────────────────
    ('polo', 'Polo'),
    ('budong', 'Budong'),
    ('bomber', 'Bomber'),
    ('chan_vay', 'Chân váy'),
    # ── Legacy (data cũ) ───────────────────────────
    ('ao_khoac', 'Áo khoác (cũ)'),
    ('gile', 'Gile (cũ)'),
]

GARMENT_STATE = [
    ('nhap', 'Nháp'),
    ('luoc', 'Lược'),
    ('lan_2', 'Lần 2'),
    ('hoan_thien', 'Hoàn thiện'),
    ('huy', 'Huỷ'),
]

# ── Thuộc tính kỹ thuật đồ may (ánh xạ sheet "Thuộc tính phụ" file DV01A) ──
HOA_TIET_VAI = [
    ('tron', 'Trơn'),
    ('ke_o_vua', 'Kẻ ô vừa'),
    ('ke_o_to', 'Kẻ ô to (trên 10cm)'),
    ('ke_doc', 'Kẻ dọc'),
    ('ke_doc_to', 'Kẻ dọc to'),
]

SO_HANG_CUC = [
    ('mot_hang', 'Một hàng cúc'),
    ('hai_hang', 'Hai hàng cúc'),
]

TUI_AO = [
    ('op', 'Ốp'),
    ('nap', 'Nắp'),
]

LOT_AO = [
    ('lot_ca', 'Lót cả'),
    ('lot_nua', 'Lót nửa'),
    ('khong_lot', 'Không lót'),
]

LO_VE = [
    ('co_lv', 'Có lơ vê'),
    ('khong_lv', 'Không lơ vê'),
]

GARMENT_LOCATION = [
    ('cua_hang', 'Cửa hàng'),
    ('ve_xuong', 'Về xưởng'),
    ('qc', 'QC (kiểm tra)'),
    ('van_phong', 'Văn phòng'),
    ('da_tra', 'Đã trả khách'),
    ('huy', 'Huỷ đồ'),
]

STEP_TYPE = [
    ('do', 'Đo'),
    ('cat', 'Cắt vải'),
    ('may', 'May thô'),
    ('luoc', 'Lược'),
    ('sua', 'Sửa'),
    ('hoan_thien', 'Hoàn thiện'),
    ('kiem_tra', 'Kiểm tra QA'),
    ('khac', 'Khác'),
]

MOVE_TYPE = [
    ('lch', 'LCH — Cửa hàng → Xưởng'),
    ('lx', 'LX — Xưởng → Cửa hàng'),
]
