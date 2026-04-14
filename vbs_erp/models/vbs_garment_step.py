# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models

STEP_TYPE = [
    ('do', 'Đo'),
    ('cat', 'Cắt vải'),
    ('may', 'May thô'),
    ('luoc', 'Lược'),
    ('sua', 'Sửa'),
    ('hoan_thien', 'Hoàn thiện'),
    ('kiem_tra', 'Kiểm tra QA'),
    ('khac', 'Khác'),
]


class VbsGarmentStep(models.Model):
    _name = 'vbs.garment.step'
    _description = 'Công đoạn may'
    _order = 'sequence, id'

    garment_id = fields.Many2one(
        'vbs.garment',
        string='Đồ may',
        required=True,
        ondelete='cascade',
        index=True,
    )

    sequence = fields.Integer(default=10)

    step_type = fields.Selection(
        STEP_TYPE,
        string='Công đoạn',
        required=True,
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Người thực hiện',
    )

    date_planned = fields.Date(string='Ngày kế hoạch')

    date_done = fields.Date(string='Ngày hoàn thành')

    duration_days = fields.Integer(
        string='Số ngày',
        compute='_compute_duration',
        store=True,
        help='Số ngày từ kế hoạch đến thực tế hoàn thành',
    )

    state = fields.Selection([
        ('todo', 'Chưa làm'),
        ('doing', 'Đang làm'),
        ('done', 'Xong'),
    ], string='Trạng thái', default='todo', required=True)

    slot_id = fields.Many2one(
        'planning.slot',
        string='Ca sản xuất',
        ondelete='set null',
        readonly=True,
    )

    note = fields.Char(string='Ghi chú')

    @api.depends('date_planned', 'date_done')
    def _compute_duration(self):
        for s in self:
            if s.date_planned and s.date_done:
                s.duration_days = (s.date_done - s.date_planned).days
            else:
                s.duration_days = 0

    def _sync_planning_slot(self):
        """Tạo hoặc cập nhật planning.slot khi step có employee + date_planned."""
        Slot = self.env['planning.slot']
        step_type_map = dict(STEP_TYPE)
        for step in self:
            if step.employee_id and step.date_planned:
                start = fields.Datetime.to_datetime(step.date_planned).replace(hour=1, minute=0)  # 08:00 UTC+7
                end = start + timedelta(hours=8)
                slot_vals = {
                    'employee_id': step.employee_id.id,
                    'garment_id': step.garment_id.id,
                    'start_datetime': start,
                    'end_datetime': end,
                    'note': step_type_map.get(step.step_type, ''),
                }
                if step.slot_id:
                    step.slot_id.write(slot_vals)
                else:
                    slot = Slot.create(slot_vals)
                    step.slot_id = slot.id
            elif step.slot_id and not step.employee_id:
                step.slot_id.unlink()
                step.slot_id = False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.filtered(lambda s: s.employee_id and s.date_planned)._sync_planning_slot()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'employee_id' in vals or 'date_planned' in vals:
            self._sync_planning_slot()
        return res
