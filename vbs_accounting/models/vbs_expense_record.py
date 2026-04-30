# -*- coding: utf-8 -*-
from odoo import api, fields, models

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

    # --- Cost allocation (optional links lên data hub) ---
    sale_order_id = fields.Many2one(
        'sale.order', string='Đơn hàng',
        ondelete='set null', index=True,
        help='Phân bổ chi phí cho đơn hàng cụ thể.',
    )
    garment_id = fields.Many2one(
        'vbs.garment', string='Đồ may',
        ondelete='set null', index=True,
        help='Phân bổ chi phí cho 1 lệnh sản xuất.',
    )
    fabric_order_id = fields.Many2one(
        'vbs.fabric.order', string='Lệnh đặt vải',
        ondelete='set null', index=True,
        help='Phân bổ chi phí cho 1 lệnh đặt vải.',
    )

    @api.onchange('garment_id')
    def _onchange_garment_id_fill_order(self):
        if self.garment_id and self.garment_id.order_id and not self.sale_order_id:
            self.sale_order_id = self.garment_id.order_id

    @api.onchange('fabric_order_id')
    def _onchange_fabric_order_fill_sale(self):
        if self.fabric_order_id and self.fabric_order_id.sale_order_id and not self.sale_order_id:
            self.sale_order_id = self.fabric_order_id.sale_order_id
