# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

FABRIC_STATE = [
    ('chua_ve', 'Chưa về'),
    ('da_ve', 'Đã về'),
]


class VbsFabricOrder(models.Model):
    _name = 'vbs.fabric.order'
    _description = 'Theo dõi đặt vải'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_order desc, id desc'
    _rec_name = 'sapo_code'

    sapo_code = fields.Char(
        string='Mã Sapo',
        index=True,
        tracking=True,
    )

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

    fabric_brand = fields.Char(
        string='Hãng vải',
        tracking=True,
    )

    fabric_type = fields.Char(
        string='Chủng loại',
        tracking=True,
    )

    stock_ids = fields.One2many(
        'vbs.fabric.stock',
        'fabric_order_id',
        string='Tồn kho từ đơn này',
    )

    quantity = fields.Float(
        string='Số lượng (m)',
        digits=(16, 3),
        tracking=True,
    )

    date_order = fields.Date(
        string='Ngày lên đơn',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )

    date_arrived = fields.Date(
        string='Ngày vải về',
        tracking=True,
    )

    lead_time = fields.Integer(
        string='Lead time (ngày)',
        compute='_compute_lead_time',
        store=True,
    )

    state = fields.Selection(
        FABRIC_STATE,
        string='Trạng thái',
        default='chua_ve',
        required=True,
        tracking=True,
        index=True,
    )

    note = fields.Text(
        string='Ghi chú',
    )

    @api.onchange('fabric_type_id')
    def _onchange_fabric_type_id(self):
        if self.fabric_type_id:
            if not self.fabric_brand:
                self.fabric_brand = self.fabric_type_id.fabric_brand
            if not self.fabric_type:
                self.fabric_type = self.fabric_type_id.name

    @api.depends('date_order', 'date_arrived')
    def _compute_lead_time(self):
        for rec in self:
            if rec.date_order and rec.date_arrived:
                rec.lead_time = (rec.date_arrived - rec.date_order).days
            else:
                rec.lead_time = 0

    def action_mark_arrived(self):
        self.write({
            'state': 'da_ve',
            'date_arrived': fields.Date.today(),
        })
