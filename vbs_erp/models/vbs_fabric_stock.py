# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VbsFabricStock(models.Model):
    _name = 'vbs.fabric.stock'
    _description = 'Tồn kho vải'
    _inherit = ['mail.thread']
    _order = 'partner_id, fabric_type'
    _rec_name = 'fabric_type'

    partner_id = fields.Many2one(
        'res.partner',
        string='Khách hàng',
        required=True,
        index=True,
        tracking=True,
    )

    fabric_type_id = fields.Many2one(
        'vbs.fabric.type',
        string='Danh mục vải',
        index=True,
        tracking=True,
        ondelete='set null',
        help='Chọn từ danh mục để liên kết giá/m tự động',
    )

    fabric_order_id = fields.Many2one(
        'vbs.fabric.order',
        string='Đơn đặt vải',
        index=True,
        tracking=True,
        ondelete='set null',
        help='Đơn đặt vải gốc tạo ra tồn kho này',
    )

    fabric_brand = fields.Char(
        string='Hãng vải',
        tracking=True,
    )

    fabric_type = fields.Char(
        string='Chủng loại vải',
        required=True,
        tracking=True,
    )

    quantity_available = fields.Float(
        string='Tồn kho (m)',
        digits=(16, 3),
        tracking=True,
    )

    note = fields.Text(
        string='Ghi chú',
        required=True,
    )

    @api.onchange('fabric_type_id')
    def _onchange_fabric_type_id(self):
        if self.fabric_type_id:
            if not self.fabric_type:
                self.fabric_type = self.fabric_type_id.name
            if not self.fabric_brand:
                self.fabric_brand = self.fabric_type_id.fabric_brand

    @api.onchange('fabric_order_id')
    def _onchange_fabric_order_id(self):
        if self.fabric_order_id:
            order = self.fabric_order_id
            if not self.partner_id:
                self.partner_id = order.partner_id
            if not self.fabric_type_id and order.fabric_type_id:
                self.fabric_type_id = order.fabric_type_id
            if not self.fabric_brand and order.fabric_brand:
                self.fabric_brand = order.fabric_brand
            if not self.fabric_type and order.fabric_type:
                self.fabric_type = order.fabric_type
