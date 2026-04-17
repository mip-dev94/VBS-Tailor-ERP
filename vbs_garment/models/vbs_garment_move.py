# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons.vbs_base.models.vbs_constants import MOVE_TYPE


class VbsGarmentMove(models.Model):
    _name = 'vbs.garment.move'
    _description = 'Lịch sử vận chuyển LCH/LX'
    _order = 'move_date asc, id asc'

    garment_id = fields.Many2one(
        'vbs.garment',
        string='Đồ',
        required=True,
        ondelete='cascade',
        index=True,
    )

    order_id = fields.Many2one(
        related='garment_id.order_id',
        string='Đơn hàng',
        store=True,
        readonly=True,
    )

    partner_id = fields.Many2one(
        related='garment_id.partner_id',
        string='Khách hàng',
        store=True,
        readonly=True,
    )

    move_type = fields.Selection(
        MOVE_TYPE,
        string='Loại',
        required=True,
    )

    move_date = fields.Datetime(
        string='Thời điểm',
        required=True,
        default=fields.Datetime.now,
    )

    trip_number = fields.Integer(
        string='Lần thứ',
        compute='_compute_trip_number',
        store=True,
    )

    duration_hours = fields.Float(
        string='Thời gian tại trạm (giờ)',
        compute='_compute_duration_hours',
        store=True,
        digits=(10, 2),
        help='Thời gian từ move này đến move tiếp theo',
    )

    note = fields.Char(string='Ghi chú')

    @api.depends('garment_id', 'garment_id.move_ids.move_date', 'move_date')
    def _compute_trip_number(self):
        for move in self:
            if not move.garment_id:
                move.trip_number = 0
                continue
            sorted_moves = move.garment_id.move_ids.sorted('move_date')
            for idx, m in enumerate(sorted_moves, 1):
                if m.id == move.id:
                    move.trip_number = idx
                    break
            else:
                move.trip_number = 0

    @api.depends('garment_id', 'garment_id.move_ids.move_date', 'move_date')
    def _compute_duration_hours(self):
        for move in self:
            if not move.garment_id:
                move.duration_hours = 0.0
                continue
            moves_list = list(move.garment_id.move_ids.sorted('move_date'))
            current_idx = next((i for i, m in enumerate(moves_list) if m.id == move.id), None)
            if current_idx is not None and current_idx + 1 < len(moves_list):
                next_move = moves_list[current_idx + 1]
                delta = next_move.move_date - move.move_date
                move.duration_hours = delta.total_seconds() / 3600
            else:
                move.duration_hours = 0.0
