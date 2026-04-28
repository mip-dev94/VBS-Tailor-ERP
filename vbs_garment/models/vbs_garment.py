# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.vbs_base.models.vbs_constants import (
    GARMENT_TYPE, GARMENT_STATE, GARMENT_LOCATION,
    HOA_TIET_VAI, SO_HANG_CUC, TUI_AO, LOT_AO, LO_VE,
)


class VbsGarment(models.Model):
    _name = 'vbs.garment'
    _description = 'Lệnh sản xuất'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'order_id, sequence, id'
    _rec_name = 'name'

    sequence = fields.Integer(default=10)

    ref = fields.Char(
        string='Mã đồ',
        readonly=True,
        copy=False,
        index=True,
        default='New',
    )

    name = fields.Char(
        string='Tên đồ',
        compute='_compute_name',
        store=True,
    )

    order_id = fields.Many2one(
        'sale.order',
        string='Đơn hàng',
        required=True,
        ondelete='cascade',
        index=True,
    )

    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Dòng đơn hàng',
        ondelete='cascade',
        index=True,
        help='Dòng sale.order.line đã sinh ra LSX này. Xoá line → cascade xoá LSX.',
    )

    partner_id = fields.Many2one(
        related='order_id.partner_id',
        string='Khách hàng',
        store=True,
        readonly=True,
        index=True,
    )

    garment_type = fields.Selection(
        GARMENT_TYPE,
        string='Loại đồ',
        required=True,
        tracking=True,
    )

    production_type = fields.Selection([
        ('nhap', 'Bản thử đo'),
    ], string='Loại LSX', default=False, tracking=True,
        help='Để trống = LSX thông thường. Bản thử đo = may prototype để kiểm tra form dáng trước khi may chính thức.')

    detail = fields.Char(
        string='Chi tiết đồ',
        help='Màu sắc, kiểu dáng, ghi chú đặc biệt',
    )

    set_type = fields.Selection([
        ('none', 'Lẻ'),
        ('bo_2', 'Bộ 2 mảnh'),
        ('bo_3', 'Bộ 3 mảnh'),
    ], string='Loại bộ', default='none')

    set_code = fields.Char(
        string='Mã bộ',
        index=True,
        help='Garment cùng mã bộ thuộc cùng 1 set (VD: SET/00001)',
    )

    state = fields.Selection(
        GARMENT_STATE,
        string='Tình trạng',
        default='luoc',
        required=True,
        tracking=True,
        index=True,
    )

    location = fields.Selection(
        GARMENT_LOCATION,
        string='Vị trí',
        default='cua_hang',
        required=True,
        tracking=True,
        index=True,
    )

    date_return = fields.Date(
        string='Ngày trả khách',
        tracking=True,
    )

    cancel_reason = fields.Char(
        string='Lý do huỷ',
        tracking=True,
    )

    date_cancelled = fields.Datetime(
        string='Ngày huỷ',
        readonly=True,
        copy=False,
    )

    move_ids = fields.One2many(
        'vbs.garment.move',
        'garment_id',
        string='Lịch sử vận chuyển',
    )

    move_count = fields.Integer(
        compute='_compute_move_count',
        string='Số lần vận chuyển',
    )

    date_state_changed = fields.Datetime(
        string='Thời điểm đổi tình trạng',
        readonly=True,
        copy=False,
    )

    days_in_current_state = fields.Integer(
        string='Số ngày ở tình trạng hiện tại',
        compute='_compute_days_in_state',
    )

    total_duration_days = fields.Integer(
        string='Tổng thời gian (ngày)',
        compute='_compute_total_duration',
        store=True,
        help='Từ lần vận chuyển đầu tiên đến ngày trả khách',
    )

    computed_price = fields.Float(
        string='Giá dự tính',
        digits=(16, 0),
        tracking=True,
        copy=False,
    )

    sapo_code = fields.Char(
        string='Mã Sapo',
        index=True,
        tracking=True,
    )

    date_entry = fields.Date(
        string='Ngày nhập',
        help='Ngày nhập đồ vào hệ thống (Ngày nhập trong sheet cũ)',
    )

    confirmed_sale = fields.Boolean(string='Sale xác nhận', tracking=True)
    confirmed_qa = fields.Boolean(string='Đã kiểm tra', tracking=True)

    # ── Người phụ trách ──────────────────────────────────────────────────────
    responsible_id = fields.Many2one(
        'res.users',
        string='Người phụ trách',
        tracking=True,
        index=True,
    )

    # ── Vải ──────────────────────────────────────────────────────────────────
    fabric_id = fields.Many2one(
        'vbs.fabric.type',
        string='Loại vải',
        tracking=True,
        index=True,
        ondelete='set null',
    )

    fabric_meters = fields.Float(
        string='Số mét vải',
        digits=(10, 2),
        help='Số mét vải cần dùng để tính giá',
    )

    fabric_note = fields.Char(
        string='Ghi chú vải',
        help='Màu sắc, chi tiết bổ sung (VD: Navy, kẻ caro)',
        tracking=True,
    )

    fabric_order_id = fields.Many2one(
        'vbs.fabric.order',
        string='Đơn đặt vải',
        help='Liên kết đơn đặt vải tương ứng',
        tracking=True,
        index=True,
        ondelete='set null',
    )

    fabric_line_id = fields.Many2one(
        'vbs.fabric.order.line',
        string='Dòng đặt vải',
        ondelete='set null',
        index=True,
        help='Dòng vải cụ thể đã đặt cho đồ này',
        copy=False,
    )

    fabric_arrived = fields.Boolean(
        string='Vải đã về',
        compute='_compute_fabric_arrived', store=True,
    )

    # ── Mã rập ───────────────────────────────────────────────────────────────
    pattern_id = fields.Many2one(
        'vbs.pattern',
        string='Mã rập',
        tracking=True,
        index=True,
        ondelete='set null',
        domain="[('garment_type', '=', garment_type)]",
    )

    # ── Mã Phiếu Kế Công ─────────────────────────────────────────────────────
    ma_pkc = fields.Char(
        string='Mã PKC',
        help='Mã Phiếu Kế Công',
        index=True,
        tracking=True,
    )

    # ── Phụ phí ──────────────────────────────────────────────────────────────
    price_surcharge = fields.Float(
        string='Phụ phí',
        digits=(16, 0),
        help='Phụ phí cộng thêm (VD: áo dài hơn áo ngắn, surcharge đặc biệt)',
    )

    # ── Kế hoạch ─────────────────────────────────────────────────────────────
    planned_date = fields.Date(
        string='Ngày kế hoạch',
        help='Deadline nội bộ hoàn thành đồ',
        tracking=True,
    )

    overdue_planned = fields.Boolean(
        string='Trễ kế hoạch',
        compute='_compute_overdue_planned',
        store=True,
    )

    # ── Thuộc tính kỹ thuật (theo sheet "Thuộc tính phụ" — file DV01A) ───────
    hoa_tiet_vai = fields.Selection(
        HOA_TIET_VAI, string='Hoạ tiết vải', tracking=True,
    )
    dai_ao = fields.Float(
        string='Dài áo (cm)', digits=(6, 1),
        help='Xưởng dùng khi cắt rập. Ánh xạ cột "Dài áo" file DV01A.',
    )
    dai_tay = fields.Float(
        string='Dài tay áo (cm)', digits=(6, 1),
    )
    so_hang_cuc = fields.Selection(
        SO_HANG_CUC, string='Số hàng cúc',
    )
    tui_ao = fields.Selection(
        TUI_AO, string='Túi áo',
    )
    lot_ao = fields.Selection(
        LOT_AO, string='Lót áo',
    )
    dai_quan = fields.Float(
        string='Dài quần (cm)', digits=(6, 1),
    )
    lo_ve = fields.Selection(
        LO_VE, string='Lơ vê',
    )

    # ── Ghi chú nội bộ ───────────────────────────────────────────────────────
    note = fields.Text(
        string='Ghi chú',
        help='Yêu cầu đặc biệt, lưu ý xưởng, v.v.',
    )

    # ── Công đoạn ────────────────────────────────────────────────────────────
    step_ids = fields.One2many(
        'vbs.garment.step',
        'garment_id',
        string='Công đoạn',
    )

    step_count = fields.Integer(
        compute='_compute_step_count',
        string='Số công đoạn',
    )

    # ── Lịch sản xuất ────────────────────────────────────────────────────────
    slot_ids = fields.One2many(
        'planning.slot',
        'garment_id',
        string='Lịch sản xuất',
    )

    slot_count = fields.Integer(
        compute='_compute_slot_count',
        string='Số ca',
    )

    sla_overdue = fields.Boolean(
        string='Quá hạn SLA',
        compute='_compute_sla_overdue',
        store=True,
    )

    @api.onchange('set_type')
    def _onchange_set_type(self):
        if self.set_type and self.set_type != 'none' and not self.set_code:
            self.set_code = self.env['ir.sequence'].next_by_code('vbs.garment.set') or ''

    @api.onchange('pattern_id')
    def _onchange_pattern_id(self):
        if not self.pattern_id:
            return
        if self.pattern_id.fabric_meters_std and not self.fabric_meters:
            self.fabric_meters = self.pattern_id.fabric_meters_std
        if self.pattern_id.preferred_fabric_type_id and not self.fabric_id:
            self.fabric_id = self.pattern_id.preferred_fabric_type_id

    @api.onchange('partner_id', 'garment_type')
    def _onchange_partner_garment_type(self):
        """Auto-suggest active custom pattern matching partner + garment_type."""
        if self.pattern_id or not self.partner_id or not self.garment_type:
            return
        pattern = self.env['vbs.pattern'].search([
            ('partner_id', '=', self.partner_id.id),
            ('garment_type', '=', self.garment_type),
            ('pattern_type', '=', 'custom'),
            ('active', '=', True),
        ], limit=1)
        if pattern:
            self.pattern_id = pattern

    @api.depends('fabric_line_id.arrived', 'fabric_order_id.state')
    def _compute_fabric_arrived(self):
        for g in self:
            if g.fabric_line_id:
                # Per-line tracking (mới): dùng arrived trên từng dòng vải
                g.fabric_arrived = g.fabric_line_id.arrived
            elif g.fabric_order_id:
                # Fallback: toàn bộ đơn da_ve
                g.fabric_arrived = g.fabric_order_id.state == 'da_ve'
            else:
                g.fabric_arrived = False

    @api.depends('garment_type', 'partner_id')
    def _compute_name(self):
        type_map = dict(GARMENT_TYPE)
        for g in self:
            type_label = type_map.get(g.garment_type, '')
            partner = g.partner_id.name or ''
            g.name = f'{partner} - {type_label}' if partner and type_label else (type_label or _('Đồ mới'))

    @api.depends('move_ids')
    def _compute_move_count(self):
        for g in self:
            g.move_count = len(g.move_ids)

    @api.depends('date_state_changed')
    def _compute_days_in_state(self):
        today = fields.Date.today()
        for g in self:
            if g.date_state_changed:
                g.days_in_current_state = (today - g.date_state_changed.date()).days
            else:
                g.days_in_current_state = 0

    @api.depends('move_ids.move_date', 'date_return')
    def _compute_total_duration(self):
        for g in self:
            moves = g.move_ids.sorted('move_date')
            if moves and g.date_return:
                first_date = moves[0].move_date.date()
                g.total_duration_days = (g.date_return - first_date).days
            else:
                g.total_duration_days = 0

    @api.depends('planned_date', 'location')
    def _compute_overdue_planned(self):
        today = fields.Date.today()
        for g in self:
            if g.planned_date and g.location not in ('da_tra', 'huy', 'van_phong'):
                g.overdue_planned = g.planned_date < today
            else:
                g.overdue_planned = False

    @api.depends('step_ids')
    def _compute_step_count(self):
        for g in self:
            g.step_count = len(g.step_ids)

    @api.depends('slot_ids')
    def _compute_slot_count(self):
        for g in self:
            g.slot_count = len(g.slot_ids)

    @api.depends('days_in_current_state', 'state', 'garment_type')
    def _compute_sla_overdue(self):
        SlaConfig = self.env['vbs.sla.config']
        for g in self:
            if not g.state or not g.garment_type:
                g.sla_overdue = False
                continue
            config = SlaConfig.search([
                ('garment_type', '=', g.garment_type),
                ('state', '=', g.state),
            ], limit=1)
            if config and config.max_days > 0:
                g.sla_overdue = g.days_in_current_state > config.max_days
            else:
                g.sla_overdue = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                vals['ref'] = self.env['ir.sequence'].next_by_code('vbs.garment') or 'New'
        records = super().create(vals_list)
        # Auto-populate steps from stage template
        StageTemplate = self.env['vbs.stage.template']
        for rec in records:
            if not rec.step_ids and rec.garment_type:
                templates = StageTemplate.search([
                    ('garment_type', '=', rec.garment_type),
                ], order='sequence')
                if templates:
                    self.env['vbs.garment.step'].create([{
                        'garment_id': rec.id,
                        'step_type': t.step_type,
                        'sequence': t.sequence,
                        'note': t.note or '',
                    } for t in templates])
        return records

    def _check_ready_for_luoc(self):
        """Kiểm tra điều kiện bắt buộc trước khi chuyển Nháp → Lược."""
        errors = []
        if not self.fabric_id:
            errors.append('• Chưa chọn Loại vải')
        if not self.fabric_meters or self.fabric_meters <= 0:
            errors.append('• Chưa điền Số mét vải')
        if not self.fabric_arrived:
            fabric_info = ''
            if self.fabric_line_id:
                fabric_info = f' (Phiếu {self.fabric_line_id.order_id.name})'
            elif self.fabric_order_id:
                fabric_info = f' ({self.fabric_order_id.name})'
            errors.append(f'• Vải chưa về kho{fabric_info}')
        if errors:
            raise UserError(_(
                'Không thể chuyển "%s" sang Lược:\n%s'
            ) % (self.ref or self.name, '\n'.join(errors)))

    # Loại đồ có 2 bước (Lược → Hoàn thiện), không có Lần 2
    _TWO_STAGE_TYPES = ['ao_khoac', 'gile', 'quan', 'quan_comple']

    def _is_two_stage(self):
        """True nếu LSX này chỉ có 2 bước: Lược → Hoàn thiện."""
        return self.production_type == 'nhap' or self.garment_type in self._TWO_STAGE_TYPES

    def write(self, vals):
        if 'state' in vals:
            new_state = vals['state']
            for rec in self:
                if rec.state == 'luoc' and new_state == 'lan_2' and rec._is_two_stage():
                    raise UserError(_(
                        'Đồ "%s" chỉ có 2 bước sản xuất: Lược → Hoàn thiện.\n'
                        'Không có bước Lần 2 cho loại đồ này.'
                    ) % (rec.ref or rec.name))
                if rec.state == 'lan_2' and new_state == 'hoan_thien' and not rec.confirmed_qa:
                    raise UserError(_('Cần QA xác nhận trước khi chuyển "%s" sang "Hoàn thiện".') % rec.ref)
                if new_state == 'huy':
                    reason = vals.get('cancel_reason', rec.cancel_reason)
                    if not reason:
                        raise UserError(_(
                            'Phải điền "Lý do huỷ" trước khi huỷ đồ %s.'
                        ) % rec.ref)
                    vals.setdefault('date_cancelled', fields.Datetime.now())
                    vals.setdefault('location', 'huy')
            vals['date_state_changed'] = fields.Datetime.now()
        result = super().write(vals)
        # CRM automation: tạo contact log khi state hoặc location thay đổi
        ICP = self.env['ir.config_parameter'].sudo()
        if 'state' in vals or 'location' in vals:
            if ICP.get_param('vbs.auto_contact_log', 'True') != 'False':
                self._create_auto_contact_log(vals)
        # VP → CH: báo sale khi đồ về văn phòng
        if vals.get('location') == 'van_phong':
            if ICP.get_param('vbs.auto_notify_sale', 'True') != 'False':
                self._notify_sale_garment_at_office()
        # Recompute stock consumed when a garment enters/leaves production
        if 'state' in vals or 'fabric_id' in vals or 'fabric_meters' in vals:
            self._trigger_stock_recompute()
        return result

    def _trigger_stock_recompute(self):
        """Recompute quantity_consumed on stock records matching (partner, fabric)."""
        Stock = self.env['vbs.fabric.stock']
        keys = {(g.partner_id.id, g.fabric_id.id) for g in self if g.partner_id and g.fabric_id}
        stocks = Stock.browse()
        for pid, fid in keys:
            stocks |= Stock.search([
                ('partner_id', '=', pid),
                ('fabric_type_id', '=', fid),
            ])
        if stocks:
            stocks._compute_quantity_consumed()
            stocks._compute_quantity_available()

    def _create_auto_contact_log(self, vals):
        """Tự động tạo nhật ký liên hệ khi tình trạng đồ thay đổi."""
        state_map = dict(GARMENT_STATE)
        location_map = dict(GARMENT_LOCATION)
        if 'vbs.contact.log' not in self.env:
            return
        ContactLog = self.env['vbs.contact.log']
        for garment in self:
            if not garment.partner_id:
                continue
            parts = []
            if 'state' in vals:
                parts.append('Tình trạng: %s' % state_map.get(vals['state'], vals['state']))
            if 'location' in vals:
                parts.append('Vị trí: %s' % location_map.get(vals['location'], vals['location']))
            noi_dung = 'Cập nhật đồ %s — %s' % (garment.ref or '', ', '.join(parts))
            ContactLog.sudo().create({
                'partner_id': garment.partner_id.id,
                'garment_id': garment.id,
                'noi_dung': noi_dung,
                'tinh_trang': 'cho_lien_he',
            })

    def _notify_sale_garment_at_office(self):
        """Tạo activity cho salesperson khi đồ về văn phòng — để báo khách."""
        activity_type = self.env.ref(
            'vbs_garment.activity_type_lien_he_khach', raise_if_not_found=False,
        )
        if not activity_type:
            return
        for garment in self:
            sale_user = garment.order_id.user_id
            if not sale_user:
                continue
            existing = garment.activity_ids.filtered(
                lambda a: a.activity_type_id == activity_type and a.summary and 'về VP' in a.summary
            )
            if not existing:
                garment.activity_schedule(
                    activity_type_id=activity_type.id,
                    summary=_('Đồ %s đã về VP — báo khách %s') % (
                        garment.ref or garment.name,
                        garment.partner_id.name or '',
                    ),
                    user_id=sale_user.id,
                )

    def action_compute_price(self):
        """Admin trigger: tính giá = vải × mét + gia công + phụ phí.
        Sau đó cộng dồn tất cả garment trong cùng order line → ghi vào price_unit.
        """
        self.ensure_one()
        fabric_cost = 0.0
        if self.fabric_id and self.fabric_meters:
            fabric_cost = self.fabric_id.price_per_meter * self.fabric_meters

        pricing = self.env['vbs.pricing.product'].search([
            ('product_type', '=', self.garment_type),
        ], limit=1)
        labor_cost = pricing.labor_cost if pricing else 0.0

        surcharge = self.price_surcharge or 0.0

        self.computed_price = fabric_cost + labor_cost + surcharge
        self._push_price_to_order_line()

    def _push_price_to_order_line(self):
        """Cộng dồn computed_price của tất cả garment cùng order_line → price_unit."""
        if not self.order_line_id:
            return
        line = self.order_line_id
        total = sum(line.garment_ids.mapped('computed_price'))
        if total:
            line.price_unit = total

    def action_view_moves(self):
        self.ensure_one()
        return {
            'name': _('Lịch sử vận chuyển'),
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.garment.move',
            'view_mode': 'list,form',
            'domain': [('garment_id', '=', self.id)],
            'context': {'default_garment_id': self.id},
        }

    def action_view_slots(self):
        self.ensure_one()
        return {
            'name': _('Lịch sản xuất'),
            'type': 'ir.actions.act_window',
            'res_model': 'planning.slot',
            'view_mode': 'calendar,list,form',
            'domain': [('garment_id', '=', self.id)],
            'context': {'default_garment_id': self.id},
        }

    def action_create_pattern(self):
        """Tạo rập mới (custom) cho khách từ garment hiện tại."""
        self.ensure_one()
        if self.pattern_id:
            return
        if not self.partner_id or not self.garment_type:
            raise UserError(_('Cần có khách hàng và loại đồ để tạo rập.'))
        pattern = self.env['vbs.pattern'].create({
            'pattern_type': 'custom',
            'partner_id': self.partner_id.id,
            'garment_type': self.garment_type,
            'fabric_meters_std': self.fabric_meters or 0.0,
            'preferred_fabric_type_id': self.fabric_id.id if self.fabric_id else False,
        })
        self.pattern_id = pattern
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.pattern',
            'res_id': pattern.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_request_fabric(self):
        """Tạo dòng đặt vải gắn vào phiếu DV01 draft của hôm nay."""
        self.ensure_one()
        if self.fabric_line_id:
            raise UserError(_('Đồ này đã có dòng đặt vải.'))
        if not self.fabric_id or not self.fabric_meters:
            raise UserError(_('Cần điền loại vải và số mét trước khi yêu cầu vải.'))
        order = self.env['vbs.fabric.order']._get_or_create_daily_draft()
        line = self.env['vbs.fabric.order.line'].create({
            'order_id': order.id,
            'garment_id': self.id,
            'partner_id': self.partner_id.id,
            'sapo_code': self.order_id.name,
            'garment_ref': self.ref,
            'fabric_type_id': self.fabric_id.id,
            'fabric_brand': self.fabric_id.fabric_brand,
            'fabric_code': self.fabric_id.code,
            'quantity': self.fabric_meters,
        })
        self.fabric_line_id = line
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.fabric.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_fabric_line(self):
        self.ensure_one()
        if not self.fabric_line_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vbs.fabric.order',
            'res_id': self.fabric_line_id.order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ── Quick-move actions (1-click transport log) ───────────────────────────

    def action_quick_lch(self):
        """Cửa hàng → Xưởng (LCH): ghi move + cập nhật vị trí."""
        for garment in self:
            self.env['vbs.garment.move'].create({
                'garment_id': garment.id,
                'move_type': 'lch',
                'move_date': fields.Datetime.now(),
            })
        self.write({'location': 've_xuong'})

    def action_quick_lx(self):
        """Xưởng → Cửa hàng (LX): ghi move + cập nhật vị trí."""
        for garment in self:
            self.env['vbs.garment.move'].create({
                'garment_id': garment.id,
                'move_type': 'lx',
                'move_date': fields.Datetime.now(),
            })
        self.write({'location': 'cua_hang'})

    def action_sale_advance_luoc(self):
        """Không còn bước Nháp — LSX mới tạo ra đã ở Lược ngay."""
        pass

    def action_quick_da_tra(self):
        """Đã trả khách: cập nhật vị trí + điền ngày trả nếu chưa có.
        Khi gọi từ tab Sale (confirmed_sale chưa set), tự động set luôn.
        """
        today = fields.Date.today()
        for garment in self:
            if garment.state != 'hoan_thien':
                raise UserError(_('Chỉ trả khách được đồ đã Hoàn thiện.'))
            vals = {'location': 'da_tra', 'confirmed_sale': True}
            if not garment.date_return:
                vals['date_return'] = today
            garment.write(vals)

    def action_confirm_qa(self):
        self.write({'confirmed_qa': True})

    def action_confirm_sale(self):
        self.write({'confirmed_sale': True})

    def action_quick_qc(self):
        self.write({'location': 'qc'})

    def action_quick_van_phong(self):
        self.write({'location': 'van_phong'})

    def action_cancel_garment(self):
        """Huỷ đồ: mở wizard hỏi lý do (hoặc huỷ luôn nếu đã có cancel_reason)."""
        active = self.filtered(lambda g: g.state != 'huy')
        if not active:
            return
        need_reason = active.filtered(lambda g: not g.cancel_reason)
        if need_reason:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'vbs.garment.cancel.wizard',
                'view_mode': 'form',
                'target': 'new',
                'name': _('Huỷ đồ'),
                'context': {'default_garment_ids': [(6, 0, active.ids)]},
            }
        active.write({'state': 'huy'})

    def action_uncancel_garment(self):
        """Admin thao tác: bỏ huỷ, đưa đồ về trạng thái nhap."""
        self.write({
            'state': 'luoc',
            'location': 'cua_hang',
            'date_cancelled': False,
        })

    def _check_sla(self):
        """Cron method: tạo activity cho garment quá hạn SLA."""
        overdue = self.search([('sla_overdue', '=', True), ('location', 'not in', ['da_tra', 'huy', 'van_phong'])])
        activity_type = self.env.ref('vbs_garment.activity_type_sla_overdue', raise_if_not_found=False)
        if not activity_type:
            return
        for garment in overdue:
            existing = garment.activity_ids.filtered(
                lambda a: a.activity_type_id == activity_type
            )
            if not existing:
                garment.activity_schedule(
                    activity_type_id=activity_type.id,
                    summary=_('Quá hạn SLA: %s đang ở "%s" quá %s ngày') % (
                        garment.name,
                        dict(GARMENT_STATE).get(garment.state, ''),
                        garment.days_in_current_state,
                    ),
                    user_id=garment.order_id.user_id.id or self.env.uid,
                )

    def _check_fitting_reminder(self):
        """Cron method: nhắc thử đồ cho garment ở state luoc/sua và ở cửa hàng."""
        ICP = self.env['ir.config_parameter'].sudo()
        if ICP.get_param('vbs.fitting_reminder', 'True') == 'False':
            return
        fitting = self.search([
            ('state', 'in', ['luoc', 'lan_2']),
            ('location', '=', 'cua_hang'),
        ])
        activity_type = self.env.ref('vbs_garment.activity_type_lien_he_khach', raise_if_not_found=False)
        if not activity_type:
            return
        for garment in fitting:
            existing = garment.activity_ids.filtered(
                lambda a: a.activity_type_id == activity_type
            )
            if not existing:
                garment.activity_schedule(
                    activity_type_id=activity_type.id,
                    summary=_('Nhắc khách thử đồ: %s') % garment.name,
                    user_id=garment.order_id.user_id.id or self.env.uid,
                )
