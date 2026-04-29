# -*- coding: utf-8 -*-
from odoo import fields, models

EXPENSE_CATEGORY = [
    ('vai', 'Chi phí vải'),
    ('gia_cong', 'Gia công / CMT'),
    ('nhan_vien', 'Nhân viên'),
    ('van_phong', 'Văn phòng / Vận hành'),
    ('khac', 'Khác'),
]


class VbsExpenseRecord(models.Model):
    _name = 'vbs.expense.record'
    _description = 'Chi phí'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Mô tả chi phí', required=True, tracking=True,
    )
    date = fields.Date(
        string='Ngày', required=True,
        default=fields.Date.context_today, tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Tiền tệ',
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary(
        string='Số tiền', required=True, tracking=True,
        currency_field='currency_id',
    )
    category = fields.Selection(
        EXPENSE_CATEGORY, string='Loại chi phí',
        required=True, default='khac', tracking=True,
    )
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(default=True)
