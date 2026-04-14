# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PlanningSlot(models.Model):
    _name = 'planning.slot'
    _description = 'Ca làm việc'
    _order = 'start_datetime'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Tiêu đề',
        compute='_compute_name',
        store=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân viên',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    role_id = fields.Many2one(
        'planning.role',
        string='Vai trò',
        tracking=True,
    )
    department_id = fields.Many2one(
        related='employee_id.department_id',
        string='Phòng ban',
        store=True,
        readonly=True,
    )
    start_datetime = fields.Datetime(
        string='Bắt đầu',
        required=True,
        tracking=True,
    )
    end_datetime = fields.Datetime(
        string='Kết thúc',
        required=True,
        tracking=True,
    )
    duration = fields.Float(
        string='Thời lượng (giờ)',
        compute='_compute_duration',
        store=True,
    )
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã huỷ'),
    ], string='Trạng thái', default='draft', tracking=True)
    color = fields.Integer(
        related='role_id.color',
        string='Màu sắc',
        store=True,
    )
    note = fields.Html(string='Ghi chú')

    @api.depends('employee_id', 'start_datetime', 'role_id')
    def _compute_name(self):
        for slot in self:
            parts = []
            if slot.employee_id:
                parts.append(slot.employee_id.name)
            if slot.role_id:
                parts.append(slot.role_id.name)
            if slot.start_datetime:
                parts.append(fields.Datetime.to_string(slot.start_datetime)[:10])
            slot.name = ' - '.join(parts) if parts else _('Ca làm việc mới')

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime:
                delta = slot.end_datetime - slot.start_datetime
                slot.duration = delta.total_seconds() / 3600
            else:
                slot.duration = 0.0

    @api.constrains('start_datetime', 'end_datetime')
    def _check_dates(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime:
                if slot.end_datetime <= slot.start_datetime:
                    raise ValidationError(_('Thời gian kết thúc phải sau thời gian bắt đầu.'))

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
