# -*- coding: utf-8 -*-
from odoo import fields, models


class VbsFabricOrderExt(models.Model):
    _inherit = 'vbs.fabric.order'

    sale_order_id = fields.Many2one(
        'sale.order', string='Đơn hàng liên kết',
        ondelete='set null', index=True,
        help='Đơn hàng khách hàng yêu cầu đặt vải này.',
    )
