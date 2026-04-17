# -*- coding: utf-8 -*-
"""Extend vbs.fabric.order.line with garment_id FK + pattern pivot.

Lives in vbs_garment (depends on vbs_fabric) to avoid circular dep.
"""
from odoo import api, fields, models


# Map garment_type selection → fabric line garment_desc selection
_GARMENT_DESC_MAP = {
    'so_mi': 'so_mi',
    'ao_khoac_le': 'ao_khoac_le',
    'quan_le': 'quan_le',
    'bo_comple_2': 'bo_comple_2',
    'bo_comple_3': 'bo_comple_3',
    'gile': 'gile',
    'ao_khoac_tao_kieu': 'ao_khoac_tao_kieu',
}


class VbsFabricOrderLineExt(models.Model):
    _inherit = 'vbs.fabric.order.line'

    garment_id = fields.Many2one(
        'vbs.garment',
        string='Đồ may',
        ondelete='set null',
        index=True,
        help='Đồ may mà dòng vải này phục vụ',
    )

    pattern_id = fields.Many2one(
        'vbs.pattern',
        string='Mã rập',
        related='garment_id.pattern_id',
        store=True,
        index=True,
    )

    @api.onchange('garment_id')
    def _onchange_garment_id(self):
        g = self.garment_id
        if not g:
            return
        if g.partner_id:
            self.partner_id = g.partner_id
        if g.order_id and not self.sapo_code:
            self.sapo_code = g.order_id.name
        if g.ref and not self.garment_ref:
            self.garment_ref = g.ref
        if g.garment_type and not self.garment_desc:
            self.garment_desc = _GARMENT_DESC_MAP.get(g.garment_type)
        if g.fabric_id and not self.fabric_type_id:
            self.fabric_type_id = g.fabric_id
            if not self.fabric_brand:
                self.fabric_brand = g.fabric_id.fabric_brand
            if not self.fabric_code:
                self.fabric_code = g.fabric_id.code
        if g.fabric_meters and not self.quantity:
            self.quantity = g.fabric_meters
