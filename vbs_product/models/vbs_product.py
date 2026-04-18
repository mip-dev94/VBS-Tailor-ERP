# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.vbs_base.models.vbs_constants import GARMENT_TYPE


class VbsProduct(models.Model):
    _name = 'vbs.product'
    _description = 'Sản phẩm B2C'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'name, id'

    name = fields.Char(string='Tên sản phẩm', required=True, tracking=True)
    code = fields.Char(string='Mã SP', readonly=True, copy=False, index=True, default='New')

    garment_type = fields.Selection(
        GARMENT_TYPE, string='Loại đồ', tracking=True, index=True,
    )
    fabric_type_id = fields.Many2one(
        'vbs.fabric.type', string='Loại vải',
        ondelete='set null', index=True, tracking=True,
    )
    size = fields.Char(string='Kích cỡ', tracking=True)
    color = fields.Char(string='Màu sắc', tracking=True)
    detail = fields.Text(string='Mô tả chi tiết')

    currency_id = fields.Many2one(
        'res.currency', string='Tiền tệ',
        default=lambda self: self.env.company.currency_id,
    )
    list_price = fields.Monetary(
        string='Giá bán', required=True, tracking=True,
        currency_field='currency_id',
    )
    cost_price = fields.Monetary(
        string='Giá vốn', tracking=True,
        currency_field='currency_id',
    )

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('ready', 'Sẵn bán'),
        ('sold', 'Đã bán'),
        ('archived', 'Ngừng bán'),
    ], string='Trạng thái', default='draft', required=True, tracking=True, index=True)

    # source_garment_id is added by vbs_garment bridge extension to avoid
    # circular dep (vbs_contact → vbs_garment would pull vbs_product).

    active = fields.Boolean(default=True)

    stock_ids = fields.One2many(
        'vbs.product.stock', 'product_id',
        string='Tồn kho theo cửa hàng',
    )
    total_available = fields.Float(
        string='Tổng tồn khả dụng',
        compute='_compute_total_available', store=True,
    )

    @api.depends('stock_ids.quantity_available')
    def _compute_total_available(self):
        for rec in self:
            rec.total_available = sum(rec.stock_ids.mapped('quantity_available'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code') or vals.get('code') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('vbs.product') or 'New'
        return super().create(vals_list)

    def action_mark_ready(self):
        for rec in self:
            if rec.list_price <= 0:
                raise UserError(_('Cần nhập giá bán trước khi đánh dấu sẵn bán.'))
            if not rec.stock_ids:
                raise UserError(_('Cần có ít nhất 1 record tồn kho trước khi đánh dấu sẵn bán.'))
            rec.state = 'ready'
            rec.message_post(body=_('Đã đánh dấu sẵn bán.'))

    def action_archive(self):
        for rec in self:
            rec.state = 'archived'
            rec.active = False
            rec.message_post(body=_('Đã ngừng bán.'))
