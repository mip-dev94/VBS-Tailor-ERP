# -*- coding: utf-8 -*-
"""Backfill arrived=True + date_arrived cho các dòng của đơn da_ve cũ.

Các đơn đã ở trạng thái da_ve trước khi có per-line arrival tracking cần
được đánh dấu tất cả dòng đã về (arrived=True) với ngày = date_arrived của đơn.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE vbs_fabric_order_line l
        SET arrived    = TRUE,
            date_arrived = COALESCE(o.date_arrived, o.date_order)
        FROM vbs_fabric_order o
        WHERE l.order_id = o.id
          AND o.state    = 'da_ve'
          AND l.arrived  = FALSE
    """)
