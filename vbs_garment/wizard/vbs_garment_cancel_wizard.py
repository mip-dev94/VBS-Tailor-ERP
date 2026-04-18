# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class VbsGarmentCancelWizard(models.TransientModel):
    _name = 'vbs.garment.cancel.wizard'
    _description = 'Huỷ đồ may — nhập lý do'

    garment_ids = fields.Many2many(
        'vbs.garment', string='Đồ cần huỷ', required=True,
    )

    reason = fields.Char(
        string='Lý do huỷ', required=True,
        help='VD: Khách đổi ý, vải hết, đơn trùng, sản xuất lỗi…',
    )

    def action_confirm(self):
        self.ensure_one()
        if not self.garment_ids:
            raise UserError(_('Không có đồ nào để huỷ.'))
        self.garment_ids.write({
            'cancel_reason': self.reason,
            'state': 'huy',
        })
        return {'type': 'ir.actions.act_window_close'}
