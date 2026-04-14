# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_type = fields.Selection([
        ('b2b', 'B2B (Vải + Gia công)'),
        ('b2c', 'B2C (Thành phẩm)'),
    ], string='Loại đơn', required=True, default='b2c', tracking=True)

    garment_ids = fields.One2many(
        'vbs.garment', 'order_id',
        string='Danh sách đồ',
    )

    garment_count = fields.Integer(
        string='Số món đồ',
        compute='_compute_garment_count',
        store=True,
    )

    @api.depends('garment_ids')
    def _compute_garment_count(self):
        for order in self:
            order.garment_count = len(order.garment_ids)

    def action_cancel(self):
        if not self.env.user.has_group('vbs_erp.group_vbs_admin'):
            raise AccessError(_('Chỉ Quản trị viên VBS mới được huỷ đơn hàng.'))
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
