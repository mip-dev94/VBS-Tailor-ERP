# -*- coding: utf-8 -*-
"""
Restore garment_ids + garment_count on vbs.pattern via _inherit.
These fields were removed from vbs_config to avoid circular dependency.
"""
from odoo import api, fields, models


class VbsPatternExt(models.Model):
    _inherit = 'vbs.pattern'

    garment_ids = fields.One2many(
        'vbs.garment',
        'pattern_id',
        string='Đồ đã may',
    )

    garment_count = fields.Integer(
        compute='_compute_garment_count',
        string='Số đồ đã may',
    )

    preferred_fabric_type_id = fields.Many2one(
        'vbs.fabric.type',
        string='Vải khách hay dùng',
        ondelete='set null',
        tracking=True,
        help='Loại vải gợi ý khi tạo đồ mới từ rập này',
    )

    last_used_date = fields.Date(
        string='Lần dùng gần nhất',
        compute='_compute_last_used_date',
        store=True,
    )

    @api.depends('garment_ids')
    def _compute_garment_count(self):
        for p in self:
            p.garment_count = len(p.garment_ids)

    @api.depends('garment_ids.create_date')
    def _compute_last_used_date(self):
        for p in self:
            dates = p.garment_ids.mapped('create_date')
            p.last_used_date = max(dates).date() if dates else False

    def action_view_garments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Đồ may từ rập này',
            'res_model': 'vbs.garment',
            'view_mode': 'list,form',
            'domain': [('pattern_id', '=', self.id)],
            'context': {'default_pattern_id': self.id},
        }
