# -*- coding: utf-8 -*-
"""Migration 2.10.0: merge da_thanh_toan → dang_xu_ly + set both confirmations = True.

Đơn hàng đang ở 'da_thanh_toan' nghĩa là đã thanh toán đủ → coi như cả 2 bên
đã xác nhận, set sale_confirmed + accountant_confirmed = True.
"""


def migrate(cr, version):
    # Thêm cột mới nếu chưa có (pre-migrate chạy trước ORM setup)
    cr.execute("""
        ALTER TABLE sale_order ADD COLUMN IF NOT EXISTS sale_confirmed boolean DEFAULT false;
        ALTER TABLE sale_order ADD COLUMN IF NOT EXISTS accountant_confirmed boolean DEFAULT false;
    """)

    # Đơn da_thanh_toan → dang_xu_ly, đánh dấu cả 2 đã xác nhận
    cr.execute("""
        UPDATE sale_order
        SET fashion_state       = 'dang_xu_ly',
            sale_confirmed      = true,
            accountant_confirmed = true
        WHERE fashion_state = 'da_thanh_toan';
    """)
