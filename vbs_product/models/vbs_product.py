# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.vbs_base.models.vbs_constants import GARMENT_TYPE


class VbsProduct(models.Model):
    _name = 'vbs.product'
    _description = 'Sản phẩm'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'name, id'

    name = fields.Char(string='Tên sản phẩm', required=True, tracking=True)
    code = fields.Char(string='Mã SP', readonly=True, copy=False, index=True, default='New')
    sku = fields.Char(string='SKU', index=True, tracking=True, help='Mã quản kho nội bộ / barcode.')

    garment_type = fields.Selection(
        GARMENT_TYPE, string='Loại đồ', tracking=True, index=True,
    )
    fabric_type_id = fields.Many2one(
        'vbs.fabric.type', string='Loại vải',
        ondelete='set null', index=True, tracking=True,
    )
    size = fields.Char(string='Kích cỡ', tracking=True)
    color = fields.Char(string='Màu sắc', tracking=True)
    weight_grams = fields.Integer(string='Trọng lượng (g)', tracking=True)
    detail = fields.Text(string='Mô tả chi tiết')

    # --- Tiền tệ ---
    currency_id = fields.Many2one(
        'res.currency', string='Tiền tệ',
        default=lambda self: self.env.company.currency_id,
    )

    # --- Giá bán ---
    list_price = fields.Monetary(
        string='Giá bán', required=True, tracking=True,
        currency_field='currency_id',
    )

    # --- Giá vốn chi tiết ---
    cost_fabric = fields.Monetary(
        string='Chi phí vải', tracking=True,
        currency_field='currency_id',
        help='Chi phí nguyên liệu vải (tính cho 1 sản phẩm).',
    )
    cost_labor = fields.Monetary(
        string='Chi phí gia công', tracking=True,
        currency_field='currency_id',
        help='Chi phí nhân công / gia công CMT.',
    )
    cost_other = fields.Monetary(
        string='Chi phí khác', tracking=True,
        currency_field='currency_id',
        help='Phụ kiện, vận chuyển, chi phí chung khác.',
    )
    cost_price = fields.Monetary(
        string='Giá vốn', tracking=True,
        currency_field='currency_id',
        help='Tổng giá vốn. Có thể nhập tay hoặc tính từ breakdown bên dưới.',
    )

    # --- Lợi nhuận (tính từ list_price - cost_price) ---
    profit_amount = fields.Monetary(
        string='Lợi nhuận', compute='_compute_profit', store=True,
        currency_field='currency_id',
    )
    profit_margin_pct = fields.Float(
        string='Biên lợi nhuận (%)', compute='_compute_profit', store=True,
        digits=(5, 1),
        help='(Giá bán - Giá vốn) / Giá bán × 100',
    )

    @api.depends('list_price', 'cost_price')
    def _compute_profit(self):
        for rec in self:
            profit = (rec.list_price or 0.0) - (rec.cost_price or 0.0)
            rec.profit_amount = profit
            rec.profit_margin_pct = (
                profit / rec.list_price * 100.0 if rec.list_price else 0.0
            )

    def action_fill_cost_from_breakdown(self):
        """Đặt Giá vốn = tổng chi phí vải + gia công + khác."""
        for rec in self:
            total = (rec.cost_fabric or 0.0) + (rec.cost_labor or 0.0) + (rec.cost_other or 0.0)
            rec.cost_price = total
            rec.message_post(body=_(
                'Giá vốn được tính từ breakdown: vải %(f)s + gia công %(l)s + khác %(o)s = %(t)s',
                f=rec.cost_fabric, l=rec.cost_labor, o=rec.cost_other, t=total,
            ))

    # --- Trạng thái ---
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('ready', 'Sẵn bán'),
        ('sold', 'Đã bán'),
        ('archived', 'Ngừng bán'),
    ], string='Trạng thái', default='draft', required=True, tracking=True, index=True)

    active = fields.Boolean(default=True)

    # --- Tồn kho ---
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
