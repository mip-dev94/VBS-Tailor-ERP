# -*- coding: utf-8 -*-
"""Extend vbs.fabric.stock with consumed/available computed from garments.

quantity_consumed = sum of fabric_meters from garments that:
  - share partner_id with this stock
  - share fabric_type_id (via fabric_id) with this stock
  - have entered production (state in 'luoc', 'lan_2', 'hoan_thien')
"""
from odoo import api, fields, models


PRODUCTION_STATES = ('luoc', 'lan_2', 'hoan_thien')


class VbsFabricStockExt(models.Model):
    _inherit = 'vbs.fabric.stock'

    quantity_consumed = fields.Float(
        string='Đã dùng (m)', digits=(16, 3),
        compute='_compute_quantity_consumed', store=True,
    )

    quantity_available = fields.Float(
        string='Còn lại (m)', digits=(16, 3),
        compute='_compute_quantity_available', store=True,
    )

    @api.depends('partner_id', 'fabric_type_id')
    def _compute_quantity_consumed(self):
        Garment = self.env['vbs.garment']
        for rec in self:
            if not rec.partner_id or not rec.fabric_type_id:
                rec.quantity_consumed = 0.0
                continue
            garments = Garment.search([
                ('partner_id', '=', rec.partner_id.id),
                ('fabric_id', '=', rec.fabric_type_id.id),
                ('state', 'in', list(PRODUCTION_STATES)),
            ])
            rec.quantity_consumed = sum(garments.mapped('fabric_meters'))

    @api.depends('quantity_received', 'quantity_consumed')
    def _compute_quantity_available(self):
        for rec in self:
            rec.quantity_available = (rec.quantity_received or 0.0) - (rec.quantity_consumed or 0.0)
