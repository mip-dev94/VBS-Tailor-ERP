# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.vbs_base.models.vbs_constants import (
    GARMENT_TYPE, GARMENT_CATEGORY, get_garment_category,
)

SET_TYPE = [
    ('le', 'Lẻ'),
    ('bo_2', 'Bộ 2 mảnh'),
    ('bo_3', 'Bộ 3 mảnh'),
]

B2B_TYPE = [
    ('ban', 'B2B Bán (Thành phẩm)'),
    ('sx',  'B2B Gia công CMT'),
]

FASHION_STATE = [
    ('dat_hang', 'Đặt hàng'),
    ('dang_xu_ly', 'Đang xử lý'),
    ('hoan_thanh', 'Hoàn thành'),
    ('huy', 'Huỷ'),
    # Legacy — migration đã chuyển sang dang_xu_ly
    ('dang_lam', 'Đang làm (cũ)'),
    ('da_thanh_toan', 'Đã thanh toán (cũ)'),
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

    b2b_type = fields.Selection(
        B2B_TYPE, string='Loại B2B', tracking=True,
        help='Bán: VBS mua vải + may + giao thành phẩm. CMT: khách mang vải, VBS chỉ gia công.',
    )

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

    amount_paid = fields.Monetary(
        string='Đã thanh toán',
        compute='_compute_payment_state', store=True,
        currency_field='currency_id',
    )
    amount_remaining = fields.Monetary(
        string='Còn lại',
        compute='_compute_payment_state', store=True,
        currency_field='currency_id',
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

    can_start_production = fields.Boolean(
        string='Có thể nhảy LSX',
        compute='_compute_can_start_production',
        help='True khi đã thanh toán ≥ 70% và đang ở trạng thái Đang xử lý',
    )

    # --- Xác nhận kép (dual confirm) để chuyển Đang xử lý → Hoàn thành ---
    sale_confirmed = fields.Boolean(
        string='Sale đã xác nhận', default=False, tracking=True,
    )
    accountant_confirmed = fields.Boolean(
        string='Kế toán đã xác nhận', default=False, tracking=True,
    )

    fabric_order_ids = fields.One2many(
        'vbs.fabric.order', 'sale_order_id',
        string='Lệnh đặt vải',
    )
    fabric_order_count = fields.Integer(
        string='Số lệnh đặt vải',
        compute='_compute_fabric_order_count',
    )

    pattern_count = fields.Integer(
        string='Số rập khách',
        compute='_compute_pattern_count',
    )

    @api.depends('garment_ids')
    def _compute_garment_count(self):
        for order in self:
            order.garment_count = len(order.garment_ids)

    def _compute_fabric_order_count(self):
        for order in self:
            order.fabric_order_count = len(order.fabric_order_ids)

    @api.depends('amount_paid', 'amount_total', 'fashion_state')
    def _compute_can_start_production(self):
        for order in self:
            order.can_start_production = (
                order.fashion_state == 'dang_xu_ly'
                and order.amount_total > 0
                and order.amount_paid >= order.amount_total * 0.7
            )

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
            order.amount_remaining = max(0.0, (order.amount_total or 0.0) - paid)
            if paid <= 0:
                order.payment_state = 'chua_tt'
            elif paid < order.amount_total:
                order.payment_state = 'tt_1_phan'
            else:
                order.payment_state = 'tt_toan_bo'

    # --- Fashion state transitions ---

    def _auto_advance_fashion_state(self):
        """Giữ để tương thích với vbs_payment_record (không còn tự động chuyển state)."""
        pass

    def _check_dual_confirm(self):
        """Kiểm tra và tự động chuyển Đang xử lý → Hoàn thành khi cả 2 bên đã xác nhận."""
        for order in self:
            if (order.fashion_state == 'dang_xu_ly'
                    and order.sale_confirmed
                    and order.accountant_confirmed):
                order.write({'fashion_state': 'hoan_thanh'})
                order.message_post(body=_(
                    'Đơn hàng hoàn thành — đã được xác nhận bởi cả Sale và Kế toán.'
                ))

    def action_sale_confirm(self):
        """Sale xác nhận đơn hàng sẵn sàng hoàn thành."""
        for order in self.filtered(lambda o: o.fashion_state == 'dang_xu_ly'):
            order.sale_confirmed = True
            order.message_post(body=_('✓ Sale đã xác nhận.'))
            order._check_dual_confirm()

    def action_accountant_confirm(self):
        """Kế toán xác nhận thanh toán và nghiệm thu."""
        for order in self.filtered(lambda o: o.fashion_state == 'dang_xu_ly'):
            order.accountant_confirmed = True
            order.message_post(body=_('✓ Kế toán đã xác nhận.'))
            order._check_dual_confirm()

    def action_confirm(self):
        """Override: sau khi confirm đơn, chuyển Đặt hàng → Đang xử lý."""
        result = super().action_confirm()
        self.filtered(lambda o: o.fashion_state == 'dat_hang').write({
            'fashion_state': 'dang_xu_ly',
            'sale_confirmed': False,
            'accountant_confirmed': False,
        })
        return result

    def action_launch_production(self):
        """Nhảy lệnh sản xuất — tạo LSX cho tất cả dòng chưa có garment (yêu cầu ≥70% thanh toán)."""
        for order in self:
            if not order.can_start_production:
                raise UserError(_(
                    'Cần thanh toán ít nhất 70%% giá trị đơn hàng trước khi nhảy lệnh sản xuất.\n'
                    'Đã thanh toán: %s / %s'
                ) % (order.amount_paid, order.amount_total))
            lines = order.order_line.filtered(
                lambda l: l.garment_type and not l.garment_ids
            )
            if not lines:
                raise UserError(_('Tất cả dòng đã có lệnh sản xuất hoặc chưa chọn loại đồ.'))
            lines.action_create_garments()

    def action_cancel(self):
        if not self.env.user.has_group('vbs_base.group_vbs_admin'):
            raise AccessError(_('Chỉ Quản trị viên VBS mới được huỷ đơn hàng.'))
        self.write({'fashion_state': 'huy', 'sale_confirmed': False, 'accountant_confirmed': False})
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

    def action_view_fabric_orders(self):
        self.ensure_one()
        return {
            'name': _('Lệnh đặt vải'),
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.fabric.order',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id},
        }

    def action_create_fabric_order(self):
        self.ensure_one()
        return {
            'name': _('Tạo lệnh đặt vải'),
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.fabric.order',
            'view_mode': 'form',
            'context': {
                'default_sale_order_id': self.id,
                'default_sapo': self.name,
            },
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

    # --- 3 filter tra giá ---
    garment_category = fields.Selection(
        GARMENT_CATEGORY, string='Loại đồ',
        help='Áo / Quần / Áo khoác — filter danh mục sản phẩm.',
    )
    set_type = fields.Selection(
        SET_TYPE, string='Hình thức',
        default='le', required=True,
        help='Lẻ / Bộ 2 mảnh / Bộ 3 mảnh. Chỉ Áo mới có Bộ 2 và Bộ 3.',
    )
    fabric_type_id = fields.Many2one(
        'vbs.fabric.type', string='Loại vải',
        ondelete='set null', index=True,
    )
    # --- Sản phẩm từ catalog vbs.product ---
    vbs_product_id = fields.Many2one(
        'vbs.product', string='Sản phẩm',
        ondelete='set null', index=True,
        help='Chọn từ catalog sản phẩm. Filter theo Loại đồ + Loại vải nếu đã chọn trước.',
    )
    # garment_type vẫn giữ để tương thích LSX, lấy từ vbs_product hoặc nhập tay
    garment_type = fields.Selection(
        GARMENT_TYPE, string='Loại đồ cụ thể',
        help='Auto-fill từ sản phẩm. Dùng để tạo LSX đúng loại.',
    )
    garment_ids = fields.One2many(
        'vbs.garment', 'order_line_id',
        string='Lệnh sản xuất',
    )
    garment_count = fields.Integer(
        string='Số LSX',
        compute='_compute_garment_count',
    )

    @api.onchange('garment_category')
    def _onchange_garment_category(self):
        """Khi đổi danh mục: reset hình thức về Lẻ nếu không phải Áo."""
        if self.garment_category != 'ao':
            self.set_type = 'le'
        self.vbs_product_id = False

    @api.onchange('vbs_product_id')
    def _onchange_vbs_product(self):
        """Khi chọn sản phẩm: auto-fill giá, garment_type, fabric_type."""
        if self.vbs_product_id:
            p = self.vbs_product_id
            self.price_unit = p.list_price or 0.0
            self.garment_type = p.garment_type or False
            if p.fabric_type_id and not self.fabric_type_id:
                self.fabric_type_id = p.fabric_type_id
            if p.garment_category and not self.garment_category:
                self.garment_category = p.garment_category

    @api.onchange('garment_category', 'set_type', 'fabric_type_id')
    def _onchange_pricing_lookup(self):
        """Tự động tra giá khi đủ 3 filter: loại đồ + hình thức + loại vải."""
        if self.vbs_product_id:
            return  # giá đã lấy từ product
        if self.garment_type and self.set_type and self.fabric_type_id:
            price = self.env['vbs.pricing.product'].lookup_price(
                garment_type=self.garment_type,
                set_type=self.set_type,
                fabric_type_id=self.fabric_type_id.id,
            )
            if price:
                self.price_unit = price

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
        """Tạo LSX từ line — chỉ được gọi qua action_launch_production (≥70% thanh toán).

        Guard server-side: kiểm tra can_start_production trên đơn hàng để chặn
        mọi đường tắt (RPC, import, automation...).
        """
        for line in self:
            order = line.order_id
            if not order.can_start_production:
                raise UserError(_(
                    'Cần thanh toán ít nhất 70%% giá trị đơn hàng trước khi tạo lệnh sản xuất.\n'
                    'Đã thanh toán: %s / %s'
                ) % (order.amount_paid, order.amount_total))
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

    def action_compute_line_price(self):
        """Tính giá tất cả LSX trong dòng này → cộng dồn vào price_unit."""
        for line in self:
            if not line.garment_ids:
                continue
            for garment in line.garment_ids:
                garment.action_compute_price()

    def action_view_line_garments(self):
        self.ensure_one()
        return {
            'name': _('Lệnh sản xuất'),
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.garment',
            'view_mode': 'list,form',
            'domain': [('order_line_id', '=', self.id)],
        }
