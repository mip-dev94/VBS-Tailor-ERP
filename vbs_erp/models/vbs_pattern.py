# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

from .vbs_garment import GARMENT_TYPE

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
        string='Dựa trên template',
        domain=[('pattern_type', '=', 'template')],
        ondelete='set null',
        tracking=True,
        help='Template rập gốc mà rập khách này được điều chỉnh từ',
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

    date_created = fields.Date(
        string='Ngày tạo rập',
        default=fields.Date.today,
    )

    active = fields.Boolean(default=True)

    note = fields.Text(
        string='Ghi chú số đo',
        help='Số đo đặc biệt, lưu ý khi may, yêu cầu riêng của khách',
    )

    garment_ids = fields.One2many(
        'vbs.garment',
        'pattern_id',
        string='Đồ đã may',
    )

    garment_count = fields.Integer(
        compute='_compute_garment_count',
        string='Số đồ đã may',
    )

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

    @api.depends('garment_ids')
    def _compute_garment_count(self):
        for p in self:
            p.garment_count = len(p.garment_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('vbs.pattern') or 'New'
        return super().create(vals_list)
