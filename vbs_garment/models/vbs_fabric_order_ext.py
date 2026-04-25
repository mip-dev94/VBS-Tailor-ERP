# -*- coding: utf-8 -*-
"""Extend vbs.fabric.order — per-line stock bump/garment notify is now handled
in VbsFabricOrderLineExt._after_line_arrived() to support partial arrivals.
"""
from odoo import models


class VbsFabricOrderExt(models.Model):
    _inherit = 'vbs.fabric.order'
