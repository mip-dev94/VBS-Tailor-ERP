# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

CONTACT_STATUS = [
    ('cho_lien_he', 'Chờ liên hệ'),
    ('da_lien_he', 'Đã liên hệ'),
]


class VbsContactLog(models.Model):
    _name = 'vbs.contact.log'
    _description = 'Nhật ký liên hệ khách hàng'
    _inherit = ['mail.thread']
    _order = 'date_contact desc, id desc'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Tên hiển thị',
        compute='_compute_display_name',
        store=True,
    )

    date_contact = fields.Date(
        string='Ngày liên hệ',
        required=True,
        default=fields.Date.today,
        tracking=True,
        index=True,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Khách hàng',
        required=True,
        index=True,
        tracking=True,
    )

    garment_id = fields.Many2one(
        'vbs.garment',
        string='Đồ may liên quan',
        index=True,
        ondelete='set null',
    )

    order_id = fields.Many2one(
        related='garment_id.order_id',
        string='Đơn hàng',
        store=True,
        readonly=True,
    )

    noi_dung = fields.Char(
        string='Nội dung liên hệ',
        help='Nội dung hoặc loại liên hệ (VD: hẹn thử đồ, báo hàng về...)',
        tracking=True,
    )

    ket_qua = fields.Char(
        string='Kết quả',
        help='Kết quả sau khi liên hệ',
        tracking=True,
    )

    tinh_trang = fields.Selection(
        CONTACT_STATUS,
        string='Tình trạng',
        default='cho_lien_he',
        required=True,
        tracking=True,
        index=True,
    )

    user_id = fields.Many2one(
        'res.users',
        string='Người liên hệ',
        default=lambda self: self.env.user,
        tracking=True,
    )

    note = fields.Text(string='Ghi chú')

    @api.depends('partner_id', 'date_contact')
    def _compute_display_name(self):
        for rec in self:
            partner = rec.partner_id.name or ''
            date = str(rec.date_contact) if rec.date_contact else ''
            rec.display_name = f'{partner} — {date}' if partner else date or _('Liên hệ mới')
