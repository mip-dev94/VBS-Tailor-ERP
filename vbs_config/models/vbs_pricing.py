# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons.vbs_base.models.vbs_constants import GARMENT_TYPE

SET_TYPE_PRICING = [
    ('le', 'Lẻ'),
    ('bo_2', 'Bộ 2 mảnh'),
    ('bo_3', 'Bộ 3 mảnh'),
]


class VbsPricingProduct(models.Model):
    """Bảng giá gia công theo 3 chiều: loại đồ × loại vải × hình thức bộ."""
    _name = 'vbs.pricing.product'
    _description = 'Bảng giá gia công'
    _order = 'garment_type, set_type, fabric_type_id'

    garment_type = fields.Selection(
        GARMENT_TYPE, string='Loại đồ', required=True, index=True,
    )
    set_type = fields.Selection(
        SET_TYPE_PRICING, string='Hình thức', required=True, default='le', index=True,
    )
    fabric_type_id = fields.Many2one(
        'vbs.fabric.type', string='Loại vải',
        ondelete='set null', index=True,
        help='Để trống = áp dụng cho mọi loại vải.',
    )

    labor_cost = fields.Float(
        string='Phí gia công (VNĐ)', digits=(16, 0), required=True, default=0.0,
    )
    note = fields.Char(string='Ghi chú')

    _sql_constraints = [
        ('unique_pricing_key',
         'UNIQUE(garment_type, set_type, fabric_type_id)',
         'Đã có giá cho tổ hợp (loại đồ + hình thức + loại vải) này.'),
    ]

    @api.model
    def lookup_price(self, garment_type, set_type='le', fabric_type_id=False):
        """Tra bảng giá với fallback 3 bước:
        1. Exact: garment_type + set_type + fabric_type_id
        2. garment_type + set_type (bất kỳ vải)
        3. garment_type + hình thức lẻ (bất kỳ vải)
        Trả về labor_cost hoặc 0.
        """
        domain_base = [('garment_type', '=', garment_type), ('set_type', '=', set_type)]

        # 1. Exact match
        if fabric_type_id:
            rec = self.search(domain_base + [('fabric_type_id', '=', fabric_type_id)], limit=1)
            if rec:
                return rec.labor_cost

        # 2. Same garment_type + set_type, no fabric filter
        rec = self.search(domain_base + [('fabric_type_id', '=', False)], limit=1)
        if rec:
            return rec.labor_cost

        # 3. Same garment_type, lẻ, no fabric (universal fallback)
        rec = self.search([
            ('garment_type', '=', garment_type),
            ('set_type', '=', 'le'),
            ('fabric_type_id', '=', False),
        ], limit=1)
        return rec.labor_cost if rec else 0.0
