# -*- coding: utf-8 -*-
"""Bỏ field `branch` khi đi về single-branch (chỉ HN).

Xoá cột `branch` trên `vbs_fabric_order_line` và field compute `branch_summary`
trên `vbs_fabric_order`. Cũng xoá sạch các record `ir.model.fields` orphan
để tránh lỗi "Field does not exist" khi load lại view.
"""


def migrate(cr, version):
    # Drop column branch trên line
    cr.execute("""
        ALTER TABLE vbs_fabric_order_line
        DROP COLUMN IF EXISTS branch
    """)
    # Drop column branch_summary trên order (stored compute)
    cr.execute("""
        ALTER TABLE vbs_fabric_order
        DROP COLUMN IF EXISTS branch_summary
    """)
    # Xoá ir.model.fields record nếu còn
    cr.execute("""
        DELETE FROM ir_model_fields
        WHERE (model = 'vbs.fabric.order.line' AND name = 'branch')
           OR (model = 'vbs.fabric.order' AND name = 'branch_summary')
    """)
    # Xoá selection values cũ
    cr.execute("""
        DELETE FROM ir_model_fields_selection
        WHERE field_id NOT IN (SELECT id FROM ir_model_fields)
    """)
