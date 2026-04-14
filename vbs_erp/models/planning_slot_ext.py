# -*- coding: utf-8 -*-
"""
Mở rộng planning.slot (từ vbs_planning) để thêm liên kết với vbs.garment.
Đặt ở vbs_erp vì vbs_erp phụ thuộc vbs_planning, không phải ngược lại.
"""
from odoo import api, fields, models, _


class PlanningSlotExt(models.Model):
    _inherit = 'planning.slot'

    garment_id = fields.Many2one(
        'vbs.garment',
        string='Đồ may',
        ondelete='set null',
        index=True,
    )

    garment_partner_id = fields.Many2one(
        related='garment_id.partner_id',
        string='Khách hàng (đồ)',
        store=True,
        readonly=True,
    )

    garment_type = fields.Selection(
        related='garment_id.garment_type',
        string='Loại đồ',
        store=True,
        readonly=True,
    )

    # Override _compute_name để thêm tên đồ vào tiêu đề ca
    @api.depends('employee_id', 'start_datetime', 'role_id', 'garment_id')
    def _compute_name(self):
        for slot in self:
            parts = []
            if slot.employee_id:
                parts.append(slot.employee_id.name)
            if slot.garment_id:
                parts.append(slot.garment_id.name)
            elif slot.role_id:
                parts.append(slot.role_id.name)
            if slot.start_datetime:
                parts.append(fields.Datetime.to_string(slot.start_datetime)[:10])
            slot.name = ' - '.join(parts) if parts else _('Ca làm việc mới')
