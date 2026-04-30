# -*- coding: utf-8 -*-
"""
Mở rộng planning.slot (từ vbs_planning) để thêm liên kết với vbs.garment.
"""
from odoo import api, fields, models, _


class PlanningSlotExt(models.Model):
    _inherit = 'planning.slot'

    garment_id = fields.Many2one(
        'vbs.garment',
        string='Đồ may',
        ondelete='cascade',
        index=True,
        help='Xoá garment → cascade xoá slot. Slot tự do (không link garment) không bị ảnh hưởng.',
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

    def action_confirm(self):
        res = super().action_confirm()
        Step = self.env['vbs.garment.step']
        Step.search([('slot_id', 'in', self.ids), ('state', '=', 'todo')]).write({'state': 'doing'})
        return res

    def action_done(self):
        res = super().action_done()
        Step = self.env['vbs.garment.step']
        steps = Step.search([('slot_id', 'in', self.ids), ('state', '!=', 'done')])
        today = fields.Date.today()
        for step in steps:
            vals = {'state': 'done'}
            if not step.date_done:
                vals['date_done'] = today
            step.write(vals)
        return res

    def action_cancel(self):
        res = super().action_cancel()
        Step = self.env['vbs.garment.step']
        Step.search([('slot_id', 'in', self.ids), ('state', '=', 'doing')]).write({'state': 'todo'})
        return res
