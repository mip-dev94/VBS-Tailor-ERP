# -*- coding: utf-8 -*-
from odoo import fields, models


class PlanningRole(models.Model):
    _name = 'planning.role'
    _description = 'Vai trò / Vị trí công việc'
    _order = 'name'

    name = fields.Char(string='Tên vai trò', required=True)
    color = fields.Integer(string='Màu sắc', default=0)
    active = fields.Boolean(default=True)
    slot_ids = fields.One2many('planning.slot', 'role_id', string='Ca làm việc')
    slot_count = fields.Integer(compute='_compute_slot_count', string='Số ca')

    def _compute_slot_count(self):
        for role in self:
            role.slot_count = len(role.slot_ids)
