# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VbsProductStock(models.Model):
    _name = 'vbs.product.stock'
    _description = 'Tồn kho sản phẩm B2C'
    _inherit = ['mail.thread']
    _order = 'partner_store_id, product_id'

    product_id = fields.Many2one(
        'vbs.product', string='Sản phẩm',
        required=True, index=True, ondelete='cascade', tracking=True,
    )
    partner_store_id = fields.Many2one(
        'res.partner', string='Cửa hàng',
        required=True, index=True, tracking=True,
    )
    quantity_on_hand = fields.Float(
        string='Tồn thực tế', default=1.0, digits=(16, 2), tracking=True,
    )
    quantity_reserved = fields.Float(
        string='Đã giữ', compute='_compute_quantity_reserved',
        store=True, digits=(16, 2),
    )
    quantity_available = fields.Float(
        string='Khả dụng', compute='_compute_quantity_available',
        store=True, digits=(16, 2),
    )
    date_received = fields.Date(
        string='Ngày nhập kho',
        default=fields.Date.context_today,
    )
    note = fields.Text(string='Ghi chú')

    _sql_constraints = [
        ('product_store_unique',
         'UNIQUE(product_id, partner_store_id)',
         'Mỗi sản phẩm tại 1 cửa hàng chỉ có 1 record tồn kho.'),
    ]

    @api.depends('product_id', 'partner_store_id')
    def _compute_quantity_reserved(self):
        # Iteration 1: chưa wire vào sale.order.line — để 0 cho đến khi tích hợp sâu.
        for rec in self:
            rec.quantity_reserved = 0.0

    @api.depends('quantity_on_hand', 'quantity_reserved')
    def _compute_quantity_available(self):
        for rec in self:
            rec.quantity_available = (rec.quantity_on_hand or 0.0) - (rec.quantity_reserved or 0.0)
