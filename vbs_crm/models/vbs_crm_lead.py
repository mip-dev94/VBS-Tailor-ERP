# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

LEAD_STAGE = [
    ('new', 'Mới'),
    ('contacted', 'Đã liên hệ'),
    ('consulting', 'Đang tư vấn'),
    ('won', 'Đã chốt đơn'),
    ('lost', 'Không chốt được'),
]

LEAD_SOURCE = [
    ('walk_in', 'Khách vãng lai'),
    ('referral', 'Giới thiệu'),
    ('facebook', 'Facebook'),
    ('instagram', 'Instagram'),
    ('website', 'Website'),
    ('other', 'Khác'),
]

LEAD_PRIORITY = [
    ('0', 'Bình thường'),
    ('1', 'Quan trọng'),
    ('2', 'Rất quan trọng'),
]


class VbsCrmLead(models.Model):
    _name = 'vbs.crm.lead'
    _description = 'Cơ hội / Lead CRM'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, date_open desc, id desc'

    # --- Thông tin cơ hội ---
    name = fields.Char(
        string='Tên cơ hội', required=True, tracking=True,
        help='Mô tả ngắn về nhu cầu hoặc tên dự án của khách.',
    )

    # --- Khách hàng ---
    partner_id = fields.Many2one(
        'res.partner', string='Khách hàng',
        tracking=True, index=True, ondelete='set null',
    )
    partner_name = fields.Char(
        string='Tên KH (chưa có hồ sơ)', tracking=True,
        help='Điền nếu khách chưa có trong danh sách liên hệ.',
    )
    phone = fields.Char(string='Số điện thoại', tracking=True)
    email = fields.Char(string='Email', tracking=True)

    # --- Pipeline ---
    stage = fields.Selection(
        LEAD_STAGE, string='Giai đoạn',
        default='new', required=True, tracking=True, index=True,
    )
    priority = fields.Selection(
        LEAD_PRIORITY, string='Ưu tiên', default='0',
    )
    source = fields.Selection(
        LEAD_SOURCE, string='Nguồn khách hàng', tracking=True,
    )
    user_id = fields.Many2one(
        'res.users', string='Nhân viên phụ trách',
        default=lambda self: self.env.user, tracking=True,
    )
    color = fields.Integer(string='Màu kanban')

    # --- Thời gian & giá trị ---
    date_open = fields.Date(
        string='Ngày tạo', default=fields.Date.context_today, tracking=True,
    )
    date_deadline = fields.Date(string='Hạn dự kiến', tracking=True)
    currency_id = fields.Many2one(
        'res.currency', string='Tiền tệ',
        default=lambda self: self.env.company.currency_id,
    )
    expected_amount = fields.Monetary(
        string='Doanh thu dự kiến', tracking=True,
        currency_field='currency_id',
    )

    # --- Nội dung ---
    note_need = fields.Text(string='Nhu cầu khách hàng')
    lost_reason = fields.Char(string='Lý do không chốt', tracking=True)

    # --- Kết quả ---
    order_id = fields.Many2one(
        'sale.order', string='Đơn hàng', readonly=True, tracking=True,
        help='Đơn hàng được tạo khi chốt lead.',
    )
    order_count = fields.Integer(
        string='Số đơn hàng', compute='_compute_order_count',
    )
    # Order summary related fields (visible khi đã chốt)
    order_amount_total = fields.Monetary(
        related='order_id.amount_total', string='Tổng đơn',
        currency_field='order_currency_id', readonly=True,
    )
    order_amount_paid = fields.Monetary(
        related='order_id.amount_paid', string='Đã thanh toán',
        currency_field='order_currency_id', readonly=True,
    )
    order_currency_id = fields.Many2one(
        related='order_id.currency_id', string='Tiền tệ đơn', readonly=True,
    )
    order_fashion_state = fields.Selection(
        related='order_id.fashion_state', string='Trạng thái VBS', readonly=True,
    )
    order_payment_state = fields.Selection(
        related='order_id.payment_state', string='Trạng thái TT', readonly=True,
    )

    active = fields.Boolean(default=True)

    @api.depends('order_id')
    def _compute_order_count(self):
        for rec in self:
            rec.order_count = 1 if rec.order_id else 0

    def action_mark_won(self):
        """Chốt lead: tạo sale.order và chuyển stage → won."""
        for rec in self:
            if rec.stage == 'won':
                continue
            partner = rec.partner_id
            if not partner and rec.partner_name:
                partner = self.env['res.partner'].create({
                    'name': rec.partner_name,
                    'phone': rec.phone,
                    'email': rec.email,
                })
                rec.partner_id = partner
            if not partner:
                raise UserError(_('Cần chọn Khách hàng hoặc nhập Tên KH trước khi chốt đơn.'))
            order = self.env['sale.order'].create({
                'partner_id': partner.id,
                'order_type': 'b2c',
            })
            rec.write({'stage': 'won', 'order_id': order.id, 'active': True})
            rec.message_post(body=_(
                'Đã chốt đơn! Đơn hàng %(name)s được tạo.',
                name=order.name,
            ))

    def action_mark_lost(self):
        """Đánh dấu lead thất bại."""
        for rec in self:
            if not rec.lost_reason:
                raise UserError(_('Vui lòng nhập Lý do không chốt trước khi đánh dấu thất bại.'))
            rec.write({'stage': 'lost'})
            rec.message_post(body=_('Không chốt được: %(reason)s', reason=rec.lost_reason))

    def action_view_order(self):
        self.ensure_one()
        if not self.order_id:
            raise UserError(_('Chưa có đơn hàng.'))
        return {
            'name': _('Đơn hàng'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.order_id.id,
        }
