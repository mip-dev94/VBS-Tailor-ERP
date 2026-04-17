# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.addons.vbs_base.models.vbs_constants import GARMENT_TYPE, GARMENT_STATE


class VbsSlaConfig(models.Model):
    _name = 'vbs.sla.config'
    _description = 'Cấu hình SLA thời gian sản xuất'
    _order = 'garment_type, state'
    _rec_name = 'display_name'

    garment_type = fields.Selection(
        GARMENT_TYPE,
        string='Loại đồ',
        required=True,
    )

    state = fields.Selection(
        GARMENT_STATE,
        string='Tình trạng',
        required=True,
    )

    max_days = fields.Integer(
        string='Số ngày tối đa',
        required=True,
        default=7,
        help='Số ngày tối đa đồ được phép ở tình trạng này. 0 = không giới hạn.',
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    def _compute_display_name(self):
        type_map = dict(GARMENT_TYPE)
        state_map = dict(GARMENT_STATE)
        for rec in self:
            t = type_map.get(rec.garment_type, '')
            s = state_map.get(rec.state, '')
            rec.display_name = f'{t} — {s}'
