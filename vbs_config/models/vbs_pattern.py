# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.vbs_base.models.vbs_constants import GARMENT_TYPE

PATTERN_TYPE = [
    ('template', 'Rập template chuẩn'),
    ('custom', 'Rập khách'),
]


class VbsPattern(models.Model):
    _name = 'vbs.pattern'
    _description = 'Mã rập'
    _inherit = ['mail.thread']
    _rec_name = 'code'
    _order = 'partner_id, garment_type, code'

    code = fields.Char(
        string='Mã rập',
        readonly=True,
        copy=False,
        index=True,
        default='New',
    )

    name = fields.Char(
        string='Tên rập',
        tracking=True,
        help='Tên mô tả tuỳ chọn (VD: Comple Anh Hùng, Áo ngắn SB Nhật Anh)',
    )

    pattern_type = fields.Selection(
        PATTERN_TYPE,
        string='Loại rập',
        required=True,
        default='custom',
        tracking=True,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Khách hàng',
        index=True,
        tracking=True,
        help='Để trống nếu là rập template chuẩn',
    )

    garment_type = fields.Selection(
        GARMENT_TYPE,
        string='Loại đồ',
        required=True,
        tracking=True,
    )

    based_on_id = fields.Many2one(
        'vbs.pattern',
        string='Dựa trên rập',
        ondelete='set null',
        tracking=True,
        help='Rập template hoặc phiên bản trước mà rập này dựa trên',
    )

    storage_location = fields.Char(
        string='Vị trí lưu',
        tracking=True,
        help='VD: Giá 3, Hàng B — để thợ tìm rập vật lý trong xưởng',
    )

    fabric_meters_std = fields.Float(
        string='Định mức vải (m)',
        digits=(10, 2),
        tracking=True,
        help='Số mét vải chuẩn cần dùng cho rập này (dùng để tính giá tự động)',
    )

    # preferred_fabric_type_id is added by vbs_garment/vbs_pattern_ext.py
    # (avoids circular dep between vbs_config and vbs_fabric)

    measurements = fields.Text(
        string='Số đo',
        help='Số đo cơ bản: dài áo, dài tay, ngực, eo, hông, dài quần...',
    )

    date_created = fields.Date(
        string='Ngày tạo rập',
        default=fields.Date.today,
    )

    # last_used_date is added by vbs_garment/vbs_pattern_ext.py
    # (depends on garment_ids which only exists in vbs_garment)

    active = fields.Boolean(default=True)

    note = fields.Text(
        string='Ghi chú số đo',
        help='Số đo đặc biệt, lưu ý khi may, yêu cầu riêng của khách',
    )

    # garment_ids and garment_count added by vbs_garment via _inherit
    # fabric_line_ids and fabric_line_count added by vbs_fabric via _inherit

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    @api.depends('code', 'partner_id', 'garment_type')
    def _compute_display_name(self):
        type_map = dict(GARMENT_TYPE)
        for p in self:
            parts = [p.code]
            if p.partner_id:
                parts.append(p.partner_id.name)
            if p.garment_type:
                parts.append(type_map.get(p.garment_type, ''))
            p.display_name = ' — '.join(filter(None, parts))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('vbs.pattern') or 'New'
        records = super().create(vals_list)
        # Auto-archive previous active custom pattern of same partner+garment_type
        for rec in records:
            if rec.pattern_type == 'custom' and rec.partner_id and rec.garment_type and rec.active:
                older = self.search([
                    ('id', '!=', rec.id),
                    ('pattern_type', '=', 'custom'),
                    ('partner_id', '=', rec.partner_id.id),
                    ('garment_type', '=', rec.garment_type),
                    ('active', '=', True),
                ])
                if older:
                    if not rec.based_on_id and len(older) == 1:
                        rec.based_on_id = older.id
                    older.write({'active': False})
        return records

    @api.constrains('pattern_type', 'partner_id', 'garment_type', 'active')
    def _check_unique_active_custom(self):
        for rec in self:
            if rec.pattern_type != 'custom' or not rec.active:
                continue
            if not rec.partner_id or not rec.garment_type:
                continue
            dup = self.search_count([
                ('id', '!=', rec.id),
                ('pattern_type', '=', 'custom'),
                ('partner_id', '=', rec.partner_id.id),
                ('garment_type', '=', rec.garment_type),
                ('active', '=', True),
            ])
            if dup:
                raise ValidationError(_(
                    'Khách "%s" đã có rập active cho loại đồ này. '
                    'Hãy lưu trữ rập cũ trước khi tạo phiên bản mới.'
                ) % rec.partner_id.name)

