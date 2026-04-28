# -*- coding: utf-8 -*-
"""Bỏ hoàn toàn bước Nháp khỏi sản xuất.

Nháp không còn là stage sản xuất. LSX mới tạo ra đã ở Lược ngay.
Các garment đang ở state='nhap' trong DB được chuyển sang 'luoc'.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE vbs_garment
        SET state = 'luoc'
        WHERE state = 'nhap'
    """)
    affected = cr.rowcount
    if affected:
        cr.execute("SELECT count(*) FROM vbs_garment WHERE state = 'nhap'")
        remaining = cr.fetchone()[0]
        assert remaining == 0, f"Migration failed: {remaining} garments still in nhap state"
