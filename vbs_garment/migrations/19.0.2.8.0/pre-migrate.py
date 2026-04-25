# -*- coding: utf-8 -*-
"""Migrate fashion_state sang state machine mới.

Cũ: dat_hang → da_thanh_toan → dang_lam → hoan_thanh
Mới: dat_hang → dang_xu_ly  → da_thanh_toan → hoan_thanh

Mapping:
  dang_lam      → da_thanh_toan  (đang làm ≈ đã thanh toán đủ)
  da_thanh_toan → dang_xu_ly     (đã TT nhưng chưa sản xuất ≈ đang xử lý)
  dat_hang + native state=sale → dang_xu_ly (đơn confirm nhưng chưa TT)
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE sale_order
        SET fashion_state = CASE fashion_state
            WHEN 'dang_lam'      THEN 'da_thanh_toan'
            WHEN 'da_thanh_toan' THEN 'dang_xu_ly'
            ELSE fashion_state
        END
        WHERE fashion_state IN ('dang_lam', 'da_thanh_toan')
    """)
    # dat_hang + đơn đã confirm (state='sale') → dang_xu_ly
    cr.execute("""
        UPDATE sale_order
        SET fashion_state = 'dang_xu_ly'
        WHERE fashion_state = 'dat_hang'
          AND state = 'sale'
    """)
