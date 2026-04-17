# -*- coding: utf-8 -*-
from odoo import api, fields, models

PAYMENT_METHOD = [
    ('cash', 'Tiền mặt'),
    ('transfer', 'Chuyển khoản'),
    ('card', 'Thẻ'),
    ('other', 'Khác'),
]


class VbsPaymentRecord(models.Model):
    _name = 'vbs.payment.record'
    _description = 'Bản ghi thanh toán'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    order_id = fields.Many2one(
        'sale.order', string='Đơn hàng',
        required=True, ondelete='cascade', index=True,
    )

    partner_id = fields.Many2one(
        related='order_id.partner_id',
        string='Khách hàng', store=True, readonly=True,
    )

    date = fields.Date(
        string='Ngày thanh toán',
        required=True, default=fields.Date.today, tracking=True,
    )

    amount = fields.Float(
        string='Số tiền (VND)',
        required=True, tracking=True,
    )

    method = fields.Selection(
        PAYMENT_METHOD, string='Phương thức',
        default='transfer', required=True, tracking=True,
    )

    note = fields.Char(string='Ghi chú', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.mapped('order_id')._auto_advance_fashion_state()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {'amount', 'order_id'} & vals.keys():
            self.mapped('order_id')._auto_advance_fashion_state()
        return res
