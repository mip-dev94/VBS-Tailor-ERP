# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

GARMENT_TYPE = [
    # ── Áo khoác / Comple ─────────────────────────
    ('ao_ngan_sb', 'Áo ngắn SB'),
    ('ao_ngan_pb', 'Áo ngắn PB'),
    ('ao_dai_sb', 'Áo dài SB'),
    ('ao_dai_pb', 'Áo dài PB'),
    ('ao_comple_sb', 'Áo Comple SB'),
    ('ao_comple_db', 'Áo Comple ĐB'),
    # ── Quần ──────────────────────────────────────
    ('quan_comple', 'Quần Comple'),
    ('quan', 'Quần'),
    # ── Sơ mi ─────────────────────────────────────
    ('so_mi', 'Sơ mi'),
    ('so_mi_tux', 'Sơ mi Tux'),
    ('so_mi_tao_kieu', 'Sơ mi tao kiểu'),
    # ── Gile ──────────────────────────────────────
    ('gile_sb', 'Gile SB'),
    ('gile_dd', 'Gile DD'),
    # ── Khác ──────────────────────────────────────
    ('polo', 'Polo'),
    ('budong', 'Budong'),
    ('bomber', 'Bomber'),
    ('chan_vay', 'Chân váy'),
    # ── Legacy (data cũ) ───────────────────────────
    ('ao_khoac', 'Áo khoác (cũ)'),
    ('gile', 'Gile (cũ)'),
    ('bo_comple', 'Bộ comple 2 mảnh (cũ)'),
    ('bo_3_manh', 'Bộ 3 mảnh (cũ)'),
]

GARMENT_STATE = [
    ('nhap', 'Nháp'),
    ('sua', 'Sửa'),
    ('luoc', 'Lược'),
    ('lan_2', 'Lần 2'),
    ('hoan_thien', 'Hoàn thiện'),
]

GARMENT_LOCATION = [
    ('cua_hang', 'Cửa hàng'),
    ('ve_xuong', 'Về xưởng'),
    ('qc', 'QC (kiểm tra)'),
    ('van_phong', 'Văn phòng'),
    ('da_tra', 'Đã trả khách'),
    ('huy', 'Huỷ đồ'),
]


class VbsGarment(models.Model):
    _name = 'vbs.garment'
    _description = 'Theo dõi đồ may'
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

    detail = fields.Char(
        string='Chi tiết đồ',
        help='Màu sắc, kiểu dáng, ghi chú đặc biệt',
    )

    state = fields.Selection(
        GARMENT_STATE,
        string='Tình trạng',
        default='nhap',
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

    confirmed_cs = fields.Boolean(string='CS xác nhận', tracking=True)
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

    @api.onchange('pattern_id')
    def _onchange_pattern_id(self):
        if self.pattern_id and self.pattern_id.fabric_meters_std and not self.fabric_meters:
            self.fabric_meters = self.pattern_id.fabric_meters_std

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

    def write(self, vals):
        if 'state' in vals:
            vals['date_state_changed'] = fields.Datetime.now()
        return super().write(vals)

    def action_compute_price(self):
        """Admin trigger: tính giá = vải × mét + gia công + phụ phí."""
        self.ensure_one()
        # 1. Chi phí vải
        fabric_cost = 0.0
        if self.fabric_id and self.fabric_meters:
            fabric_cost = self.fabric_id.price_per_meter * self.fabric_meters

        # 2. Chi phí gia công (theo loại sản phẩm)
        pricing = self.env['vbs.pricing.product'].search([
            ('product_type', '=', self.garment_type),
        ], limit=1)
        labor_cost = pricing.labor_cost if pricing else 0.0

        # 3. Phụ phí
        surcharge = self.price_surcharge or 0.0

        self.computed_price = fabric_cost + labor_cost + surcharge

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

    def action_quick_da_tra(self):
        """Đã trả khách: cập nhật vị trí + điền ngày trả nếu chưa có."""
        today = fields.Date.today()
        for garment in self:
            vals = {'location': 'da_tra'}
            if not garment.date_return:
                vals['date_return'] = today
            garment.write(vals)

    def action_quick_qc(self):
        self.write({'location': 'qc'})

    def action_quick_van_phong(self):
        self.write({'location': 'van_phong'})

    def _check_sla(self):
        """Cron method: tạo activity cho garment quá hạn SLA."""
        overdue = self.search([('sla_overdue', '=', True), ('location', 'not in', ['da_tra', 'huy', 'van_phong'])])
        activity_type = self.env.ref('vbs_erp.activity_type_sla_overdue', raise_if_not_found=False)
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
