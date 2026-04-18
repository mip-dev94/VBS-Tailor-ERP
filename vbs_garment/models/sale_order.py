# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.vbs_base.models.vbs_constants import GARMENT_TYPE

SET_TYPE = [
    ('le', 'Lẻ'),
    ('bo_2', 'Bộ 2 mảnh'),
    ('bo_3', 'Bộ 3 mảnh'),
]

FASHION_STATE = [
    ('dat_hang', 'Đặt hàng'),
    ('da_thanh_toan', 'Đã thanh toán'),
    ('dang_lam', 'Đang làm'),
    ('hoan_thanh', 'Hoàn thành'),
    ('huy', 'Huỷ'),
]

PAYMENT_STATE = [
    ('chua_tt', 'Chưa thanh toán'),
    ('tt_1_phan', 'Thanh toán 1 phần'),
    ('tt_toan_bo', 'Thanh toán toàn bộ'),
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_type = fields.Selection([
        ('b2b', 'B2B (Vải + Gia công)'),
        ('b2c', 'B2C (Thành phẩm)'),
        ('sua', 'Sửa (Đồ khách)'),
    ], string='Loại đơn', required=True, default='b2c', tracking=True)

    fashion_state = fields.Selection(
        FASHION_STATE, string='Trạng thái VBS',
        default='dat_hang', required=True, tracking=True, index=True,
    )

    payment_state = fields.Selection(
        PAYMENT_STATE, string='Thanh toán',
        compute='_compute_payment_state', store=True, tracking=True,
    )

    payment_ids = fields.One2many(
        'vbs.payment.record', 'order_id',
        string='Lịch sử thanh toán',
    )

    amount_paid = fields.Float(
        string='Đã thanh toán (VND)',
        compute='_compute_payment_state', store=True,
    )

    garment_ids = fields.One2many(
        'vbs.garment', 'order_id',
        string='Danh sách đồ',
    )

    garment_count = fields.Integer(
        string='Số món đồ',
        compute='_compute_garment_count',
        store=True,
    )

    pattern_count = fields.Integer(
        string='Số rập khách',
        compute='_compute_pattern_count',
    )

    @api.depends('garment_ids')
    def _compute_garment_count(self):
        for order in self:
            order.garment_count = len(order.garment_ids)

    @api.depends('partner_id')
    def _compute_pattern_count(self):
        Pattern = self.env['vbs.pattern']
        for order in self:
            if order.partner_id:
                order.pattern_count = Pattern.search_count([
                    ('partner_id', '=', order.partner_id.id),
                    ('active', '=', True),
                ])
            else:
                order.pattern_count = 0

    # Constraint cũ tách B2B/B2C đã gỡ: giờ 1 đơn có thể vừa có order_line
    # (thành phẩm có sẵn / đồ đã hoàn thiện tái bán) vừa có garment_ids
    # (lệnh sản xuất auto-sinh từ line). order_type chỉ để filter báo cáo.

    @api.depends('payment_ids.amount', 'amount_total')
    def _compute_payment_state(self):
        for order in self:
            paid = sum(order.payment_ids.mapped('amount'))
            order.amount_paid = paid
            if paid <= 0:
                order.payment_state = 'chua_tt'
            elif paid < order.amount_total:
                order.payment_state = 'tt_1_phan'
            else:
                order.payment_state = 'tt_toan_bo'

    # --- Fashion state transitions ---

    def action_fashion_confirm_payment(self):
        """Đặt hàng → Đã thanh toán."""
        self.filtered(lambda o: o.fashion_state == 'dat_hang').write({
            'fashion_state': 'da_thanh_toan',
        })

    def _auto_advance_fashion_state(self):
        """Gọi sau khi payment_record thay đổi — auto chuyển dat_hang→da_thanh_toan."""
        for order in self:
            if order.payment_state == 'tt_toan_bo' and order.fashion_state == 'dat_hang':
                order.fashion_state = 'da_thanh_toan'

    def action_fashion_start_production(self):
        """Đã thanh toán → Đang làm."""
        self.filtered(lambda o: o.fashion_state == 'da_thanh_toan').write({
            'fashion_state': 'dang_lam',
        })

    def action_fashion_complete(self):
        """Đang làm → Hoàn thành."""
        self.filtered(lambda o: o.fashion_state == 'dang_lam').write({
            'fashion_state': 'hoan_thanh',
        })

    def action_cancel(self):
        if not self.env.user.has_group('vbs_base.group_vbs_admin'):
            raise AccessError(_('Chỉ Quản trị viên VBS mới được huỷ đơn hàng.'))
        self.write({'fashion_state': 'huy'})
        return super().action_cancel()

    def action_view_garments(self):
        self.ensure_one()
        return {
            'name': _('Đồ may'),
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.garment',
            'view_mode': 'list,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }

    def action_view_patterns(self):
        self.ensure_one()
        return {
            'name': _('Rập của khách'),
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.pattern',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_pattern_type': 'custom',
            },
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    set_type = fields.Selection(
        SET_TYPE, string='Loại bộ',
        default='le', required=True,
        help='Lẻ → 1 lệnh sản xuất. Bộ 2 mảnh → 2 (áo + quần). Bộ 3 mảnh → 3 (áo + quần + gile).',
    )
    garment_type = fields.Selection(
        GARMENT_TYPE, string='Loại đồ',
        help='Loại đồ chính (phần áo khi là bộ). Để trống nếu là hàng thành phẩm B2C có sẵn.',
    )
    garment_ids = fields.One2many(
        'vbs.garment', 'order_line_id',
        string='Lệnh sản xuất',
    )
    garment_count = fields.Integer(
        string='Số LSX',
        compute='_compute_garment_count',
    )

    @api.depends('garment_ids')
    def _compute_garment_count(self):
        for line in self:
            line.garment_count = len(line.garment_ids)

    def _get_set_components(self):
        """Trả list garment_type cần tạo dựa trên set_type + garment_type chính.

        Mapping:
         - Lẻ         → [main]
         - Bộ 2 mảnh → [main, quần tương ứng]
         - Bộ 3 mảnh → [main, quần, gile]
        Quần = quan_comple nếu áo là comple, quan (thường) nếu khác.
        Gile  = gile_dd nếu áo DB, gile_sb nếu SB/khác.
        """
        self.ensure_one()
        main = self.garment_type
        if not main:
            return []
        if self.set_type == 'le':
            return [main]
        is_comple = 'comple' in main
        is_db = main.endswith('_db')
        pants = 'quan_comple' if is_comple else 'quan'
        gile = 'gile_dd' if is_db else 'gile_sb'
        if self.set_type == 'bo_2':
            return [main, pants]
        if self.set_type == 'bo_3':
            return [main, pants, gile]
        return [main]

    def action_create_garments(self):
        """Nút thủ công: tạo các lệnh sản xuất (vbs.garment) từ line này.

        Idempotent — nếu line đã có garment_ids → raise UserError để user
        xoá trước (xoá line cũng cascade xoá garment).
        """
        Garment = self.env['vbs.garment']
        created = Garment.browse()
        for line in self:
            if not line.garment_type:
                raise UserError(_(
                    'Dòng "%s" chưa chọn Loại đồ — không thể tạo lệnh sản xuất.'
                ) % (line.product_id.display_name or line.name or ''))
            if line.garment_ids:
                raise UserError(_(
                    'Dòng "%s" đã có %d lệnh sản xuất. '
                    'Xoá lệnh cũ trước khi tạo mới.'
                ) % (line.product_id.display_name or line.name or '', len(line.garment_ids)))
            components = line._get_set_components()
            set_code = False
            if line.set_type in ('bo_2', 'bo_3'):
                set_code = self.env['ir.sequence'].next_by_code('vbs.garment.set') or False
            for idx, gtype in enumerate(components):
                created |= Garment.create({
                    'order_id': line.order_id.id,
                    'order_line_id': line.id,
                    'garment_type': gtype,
                    'set_type': (
                        'none' if line.set_type == 'le'
                        else ('bo_2' if line.set_type == 'bo_2' else 'bo_3')
                    ),
                    'set_code': set_code,
                    'detail': line.name or '',
                    'sequence': (idx + 1) * 10,
                })
        if not created:
            return True
        return {
            'name': _('Lệnh sản xuất vừa tạo'),
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.garment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created.ids)],
        }

    def action_view_line_garments(self):
        self.ensure_one()
        return {
            'name': _('Lệnh sản xuất'),
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.garment',
            'view_mode': 'list,form',
            'domain': [('order_line_id', '=', self.id)],
        }
