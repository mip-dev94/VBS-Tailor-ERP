# -*- coding: utf-8 -*-
from odoo import api, fields, models


INSPECTION_STATE = [
    ('chua_kt', 'Chưa kiểm tra'),
    ('da_kt', 'Đã kiểm tra'),
]

GARMENT_DESC = [
    ('so_mi', '01 sơ mi'),
    ('ao_khoac_le', '01 áo khoác lẻ'),
    ('quan_le', '01 quần lẻ'),
    ('bo_comple_2', '01 bộ comple 2 mảnh'),
    ('bo_comple_3', '01 bộ comple 3 mảnh'),
    ('gile', '01 gile'),
    ('ao_khoac_tao_kieu', '01 áo khoác tạo kiểu'),
    ('lot_ao_khoac', '01 lót áo khoác'),
    ('bo_cuc', '01 bộ cúc'),
    ('khac', 'Khác'),
]

PATTERN = [
    ('tron', 'Trơn'),
    ('ke_o_vua', 'Kẻ ô vừa'),
    ('ke_o_to', 'Kẻ ô to (trên 10cm)'),
    ('ke_doc', 'Kẻ dọc'),
    ('ke_doc_to', 'Kẻ dọc to'),
]

BUTTON_ROW = [
    ('mot_hang', 'Một hàng cúc'),
    ('hai_hang', 'Hai hàng cúc'),
]

POCKET = [
    ('op', 'Ốp'),
    ('nap', 'Nắp'),
]

LINING = [
    ('lot_ca', 'Lót cả'),
    ('lot_nua', 'Lót nửa'),
    ('khong_lot', 'Không lót'),
]

CUFF = [
    ('co_lv', 'Có lơ vê'),
    ('khong_lv', 'Không lơ vê'),
]


class VbsFabricOrderLine(models.Model):
    _name = 'vbs.fabric.order.line'
    _description = 'Dòng đặt vải'
    _order = 'sequence, id'

    order_id = fields.Many2one(
        'vbs.fabric.order', string='Phiếu đặt vải',
        required=True, ondelete='cascade', index=True,
    )

    sequence = fields.Integer(string='STT', default=10)

    # ── Khách (mỗi dòng độc lập) ──────────────────────
    partner_id = fields.Many2one(
        'res.partner', string='Khách hàng',
        required=True, index=True,
        domain=[('user_ids', '=', False)],
    )
    sapo_code = fields.Char(string='Mã Sapo', index=True)
    garment_ref = fields.Char(string='Mã đồ', index=True)
    inspection_state = fields.Selection(
        INSPECTION_STATE, string='Kiểm tra',
        default='chua_kt',
    )

    # ── Vải ─────────────────────────────────────────────────────────
    fabric_type_id = fields.Many2one(
        'vbs.fabric.type', string='Danh mục vải',
        index=True, ondelete='set null',
        help='Chọn từ danh mục để tự động điền hãng/chủng loại',
    )
    fabric_brand = fields.Char(string='Hãng vải')
    fabric_code = fields.Char(string='Mã vải')

    # ── Đồ ──────────────────────────────────────────────────────────
    garment_desc = fields.Selection(
        GARMENT_DESC, string='Mô tả đồ đặt',
        help='01 sơ mi / 01 áo khoác lẻ / 01 bộ comple...',
    )

    quantity = fields.Float(
        string='Khối lượng (m)', digits=(16, 3),
        help='Xưởng tính toán và điền khối lượng vải',
    )

    pattern = fields.Selection(
        PATTERN, string='Hoạ tiết vải',
        help='Trơn / Kẻ ô / Kẻ dọc — ảnh hưởng tới khối lượng vải',
    )

    dai_ao = fields.Char(string='Dài áo')
    dai_tay_ao = fields.Char(string='Dài tay áo')
    dai_quan = fields.Char(string='Dài quần')

    button_row = fields.Selection(BUTTON_ROW, string='Số hàng cúc')
    pocket = fields.Selection(POCKET, string='Túi áo')
    lining = fields.Selection(LINING, string='Lót áo')
    cuff = fields.Selection(CUFF, string='Lơ vê')

    note = fields.Char(string='Ghi chú')

    state = fields.Selection(related='order_id.state', string='Trạng thái', store=True)

    arrived = fields.Boolean(string='Đã về', default=False, index=True)
    date_arrived = fields.Date(string='Ngày về')

    def action_toggle_inspection(self):
        """Toggle trạng thái kiểm tra: Chưa kiểm tra ↔ Đã kiểm tra."""
        for rec in self:
            if rec.inspection_state == 'chua_kt':
                rec.inspection_state = 'da_kt'
            else:
                rec.inspection_state = 'chua_kt'

    def action_mark_line_arrived(self):
        """Đánh dấu dòng vải này đã về kho."""
        today = fields.Date.today()
        newly = self.filtered(lambda l: not l.arrived)
        if newly:
            newly.write({'arrived': True, 'date_arrived': today})
            newly._after_line_arrived()
            newly.mapped('order_id')._check_all_arrived()

    def _after_line_arrived(self):
        """Hook cho submodule mở rộng khi từng dòng vải về (vd: cập nhật stock, tạo activity)."""
        pass

    @api.onchange('fabric_type_id')
    def _onchange_fabric_type_id(self):
        if self.fabric_type_id:
            if not self.fabric_brand:
                self.fabric_brand = self.fabric_type_id.fabric_brand
            if not self.fabric_code:
                self.fabric_code = self.fabric_type_id.code
