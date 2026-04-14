# -*- coding: utf-8 -*-
from odoo import fields, models

from .vbs_garment import GARMENT_TYPE
from .vbs_garment_step import STEP_TYPE


class VbsStageTemplate(models.Model):
    _name = 'vbs.stage.template'
    _description = 'Template công đoạn theo loại đồ'
    _order = 'garment_type, sequence'

    garment_type = fields.Selection(
        GARMENT_TYPE,
        string='Loại đồ',
        required=True,
        index=True,
    )

    sequence = fields.Integer(default=10)

    step_type = fields.Selection(
        STEP_TYPE,
        string='Công đoạn',
        required=True,
    )

    note = fields.Char(string='Ghi chú mặc định')

    _sql_constraints = [
        ('unique_garment_step', 'UNIQUE(garment_type, step_type)',
         'Mỗi loại đồ chỉ có 1 template cho mỗi công đoạn.'),
    ]
