# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError

FASHION_STATE = [
    ('dat_hang', 'Đặt hàng'),
    ('da_thanh_toan', 'Đã thanh toán'),
    ('dang_lam', 'Đang làm'),
    ('hoan_thanh', 'Hoàn thành'),
    ('huy', 'Huỷ'),
]

PAYMENT_STATE = [
    ('chua_tt', 'Chưa thanh toán'),
    ('tt_1_phan', 'Thanh toán 1 phần'),
    ('tt_toan_bo', 'Thanh toán toàn bộ'),
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_type = fields.Selection([
        ('b2b', 'B2B (Vải + Gia công)'),
        ('b2c', 'B2C (Thành phẩm)'),
        ('sua', 'Sửa (Đồ khách)'),
    ], string='Loại đơn', required=True, default='b2c', tracking=True)

    fashion_state = fields.Selection(
        FASHION_STATE, string='Trạng thái VBS',
        default='dat_hang', required=True, tracking=True, index=True,
    )

    payment_state = fields.Selection(
        PAYMENT_STATE, string='Thanh toán',
        compute='_compute_payment_state', store=True, tracking=True,
    )

    payment_ids = fields.One2many(
        'vbs.payment.record', 'order_id',
        string='Lịch sử thanh toán',
    )

    amount_paid = fields.Float(
        string='Đã thanh toán (VND)',
        compute='_compute_payment_state', store=True,
    )

    garment_ids = fields.One2many(
        'vbs.garment', 'order_id',
        string='Danh sách đồ',
    )

    garment_count = fields.Integer(
        string='Số món đồ',
        compute='_compute_garment_count',
        store=True,
    )

    pattern_count = fields.Integer(
        string='Số rập khách',
        compute='_compute_pattern_count',
    )

    @api.depends('garment_ids')
    def _compute_garment_count(self):
        for order in self:
            order.garment_count = len(order.garment_ids)

    @api.depends('partner_id')
    def _compute_pattern_count(self):
        Pattern = self.env['vbs.pattern']
        for order in self:
            if order.partner_id:
                order.pattern_count = Pattern.search_count([
                    ('partner_id', '=', order.partner_id.id),
                    ('active', '=', True),
                ])
            else:
                order.pattern_count = 0

    @api.depends('payment_ids.amount', 'amount_total')
    def _compute_payment_state(self):
        for order in self:
            paid = sum(order.payment_ids.mapped('amount'))
            order.amount_paid = paid
            if paid <= 0:
                order.payment_state = 'chua_tt'
            elif paid < order.amount_total:
                order.payment_state = 'tt_1_phan'
            else:
                order.payment_state = 'tt_toan_bo'

    # --- Fashion state transitions ---

    def action_fashion_confirm_payment(self):
        """Đặt hàng → Đã thanh toán."""
        self.filtered(lambda o: o.fashion_state == 'dat_hang').write({
            'fashion_state': 'da_thanh_toan',
        })

    def _auto_advance_fashion_state(self):
        """Gọi sau khi payment_record thay đổi — auto chuyển dat_hang→da_thanh_toan."""
        for order in self:
            if order.payment_state == 'tt_toan_bo' and order.fashion_state == 'dat_hang':
                order.fashion_state = 'da_thanh_toan'

    def action_fashion_start_production(self):
        """Đã thanh toán → Đang làm."""
        self.filtered(lambda o: o.fashion_state == 'da_thanh_toan').write({
            'fashion_state': 'dang_lam',
        })

    def action_fashion_complete(self):
        """Đang làm → Hoàn thành."""
        self.filtered(lambda o: o.fashion_state == 'dang_lam').write({
            'fashion_state': 'hoan_thanh',
        })

    def action_cancel(self):
        if not self.env.user.has_group('vbs_base.group_vbs_admin'):
            raise AccessError(_('Chỉ Quản trị viên VBS mới được huỷ đơn hàng.'))
        self.write({'fashion_state': 'huy'})
        return super().action_cancel()

    def action_view_garments(self):
        self.ensure_one()
        return {
            'name': _('Đồ may'),
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.garment',
            'view_mode': 'list,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }

    def action_view_patterns(self):
        self.ensure_one()
        return {
            'name': _('Rập của khách'),
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.pattern',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_pattern_type': 'custom',
            },
        }
