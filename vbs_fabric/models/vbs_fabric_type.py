# -*- coding: utf-8 -*-
from odoo import fields, models


class VbsFabricType(models.Model):
    _name = 'vbs.fabric.type'
    _description = 'Danh mục loại vải'
    _order = 'fabric_brand, name'

    code = fields.Char(
        string='Mã vải',
        required=True,
        index=True,
        help='Mã nội bộ hoặc mã Sapo',
    )

    name = fields.Char(
        string='Tên vải',
        required=True,
    )

    fabric_brand = fields.Char(
        string='Hãng vải',
        help='Drago, VBC, Loro Piana, Hesworth...',
    )

    price_per_meter = fields.Float(
        string='Giá/mét (VNĐ)',
        digits=(16, 0),
        required=True,
    )

    note = fields.Char(string='Ghi chú')

    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        """Hiển thị: Hãng — Mã — Tên (vd: Drago — DR001 — Vải len)."""
        for r in self:
            parts = [r.code, r.name]
            if r.fabric_brand:
                parts.insert(0, r.fabric_brand)
            r.display_name = ' — '.join(filter(None, parts))
