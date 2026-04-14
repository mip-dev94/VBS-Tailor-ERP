# -*- coding: utf-8 -*-
from odoo import fields, models
from .vbs_garment import GARMENT_TYPE


class VbsPricingProduct(models.Model):
    """Bảng giá gia công theo loại sản phẩm."""
    _name = 'vbs.pricing.product'
    _description = 'Giá gia công theo loại sản phẩm'
    _order = 'product_type'

    product_type = fields.Selection(
        GARMENT_TYPE,
        string='Loại sản phẩm',
        required=True,
    )

    labor_cost = fields.Float(
        string='Phí gia công (VNĐ)',
        digits=(16, 0),
        required=True,
    )

    note = fields.Char(string='Ghi chú')

    _sql_constraints = [
        ('unique_product_type', 'UNIQUE(product_type)',
         'Đã có giá gia công cho loại sản phẩm này.'),
    ]
