# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

FABRIC_ORDER_STATE = [
    ('draft', 'DV01 — Chờ duyệt'),
    ('cho_dat', 'DV02 — Chờ đặt'),
    ('cho_ve', 'DV03 — Chờ vải về'),
    ('da_ve', 'DV04 — Vải đã về'),
]


class VbsFabricOrder(models.Model):
    _name = 'vbs.fabric.order'
    _description = 'Phiếu đặt vải (DV01A)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_order desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Số phiếu', required=True, copy=False,
        default=lambda self: _('Mới'), tracking=True,
    )

    date_order = fields.Date(
        string='Ngày lập phiếu', required=True,
        default=fields.Date.today, tracking=True,
    )

    date_approved = fields.Date(
        string='Ngày kế toán duyệt', tracking=True, readonly=True,
    )

    date_arrived = fields.Date(string='Ngày vải về', tracking=True)

    lead_time = fields.Integer(
        string='Lead time (ngày)',
        compute='_compute_lead_time', store=True,
    )

    days_since_approved = fields.Integer(
        string='Số ngày từ khi đặt',
        compute='_compute_days_since_approved',
    )

    state = fields.Selection(
        FABRIC_ORDER_STATE, string='Trạng thái',
        default='draft', required=True, tracking=True, index=True,
    )

    approved_by = fields.Many2one(
        'res.users', string='Kế toán duyệt', readonly=True, tracking=True,
    )

    line_ids = fields.One2many(
        'vbs.fabric.order.line', 'order_id',
        string='Danh sách vải',
    )

    stock_ids = fields.One2many(
        'vbs.fabric.stock', 'fabric_order_id',
        string='Tồn kho từ đơn này',
    )

    # Aggregates cho header hiển thị / tìm kiếm
    partner_ids = fields.Many2many(
        'res.partner', string='Khách hàng',
        compute='_compute_partner_ids', store=True,
    )

    line_count = fields.Integer(
        string='Số dòng', compute='_compute_line_count',
    )

    arrived_line_count = fields.Integer(
        string='Dòng đã về',
        compute='_compute_arrived_counts', store=True,
    )
    pending_line_count = fields.Integer(
        string='Dòng chưa về',
        compute='_compute_arrived_counts', store=True,
    )

    total_quantity = fields.Float(
        string='Tổng khối lượng (m)', digits=(16, 3),
        compute='_compute_total_quantity', store=True,
    )

    note = fields.Text(string='Ghi chú')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                seq = self.env['ir.sequence'].next_by_code('vbs.fabric.order')
                vals['name'] = seq or _('Mới')
        return super().create(vals_list)

    @api.depends('line_ids.partner_id')
    def _compute_partner_ids(self):
        for rec in self:
            rec.partner_ids = rec.line_ids.mapped('partner_id')

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.depends('line_ids.arrived')
    def _compute_arrived_counts(self):
        for rec in self:
            arrived = rec.line_ids.filtered('arrived')
            rec.arrived_line_count = len(arrived)
            rec.pending_line_count = len(rec.line_ids) - len(arrived)

    @api.depends('line_ids.quantity')
    def _compute_total_quantity(self):
        for rec in self:
            rec.total_quantity = sum(rec.line_ids.mapped('quantity'))

    @api.depends('date_order', 'date_arrived')
    def _compute_lead_time(self):
        for rec in self:
            if rec.date_order and rec.date_arrived:
                rec.lead_time = (rec.date_arrived - rec.date_order).days
            else:
                rec.lead_time = 0

    @api.depends('date_approved')
    def _compute_days_since_approved(self):
        today = fields.Date.today()
        for rec in self:
            if rec.date_approved:
                rec.days_since_approved = (today - rec.date_approved).days
            else:
                rec.days_since_approved = 0

    # --- State transition actions ---

    def action_approve(self):
        """DV01 → DV02: Kế toán duyệt đơn."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Chỉ đơn ở trạng thái DV01 mới được duyệt.'))
            if not rec.line_ids:
                raise UserError(_('Phiếu đặt vải phải có ít nhất 1 dòng.'))
        self.write({
            'state': 'cho_dat',
            'date_approved': fields.Date.today(),
            'approved_by': self.env.uid,
        })

    def action_confirm_ordered(self):
        """DV02 → DV03: Xác nhận đã đặt vải (kế toán)."""
        for rec in self:
            if rec.state != 'cho_dat':
                raise UserError(_('Chỉ đơn ở trạng thái DV02 mới chuyển sang DV03.'))
        self.write({'state': 'cho_ve'})

    def action_mark_arrived(self):
        """DV03 → DV04: Đánh dấu tất cả dòng vải chưa về là đã về (bulk shortcut)."""
        for rec in self:
            if rec.state != 'cho_ve':
                raise UserError(_('Chỉ đơn ở trạng thái DV03 mới chuyển sang DV04.'))
        pending = self.mapped('line_ids').filtered(lambda l: not l.arrived)
        if pending:
            pending.action_mark_line_arrived()
        else:
            self._check_all_arrived()

    def _check_all_arrived(self):
        """Tự động chuyển sang da_ve khi tất cả dòng đều đánh dấu đã về."""
        for rec in self:
            if rec.state != 'cho_ve':
                continue
            if not rec.line_ids:
                continue
            if all(l.arrived for l in rec.line_ids):
                last_date = max(
                    (l.date_arrived for l in rec.line_ids if l.date_arrived),
                    default=fields.Date.today(),
                )
                rec.write({'state': 'da_ve', 'date_arrived': last_date})
                ICP = self.env['ir.config_parameter'].sudo()
                if ICP.get_param('vbs.auto_contact_log', 'True') != 'False':
                    rec._create_fabric_arrived_contact_log()

    def _create_fabric_arrived_contact_log(self):
        """Tự động tạo nhật ký liên hệ — nhóm theo khách hàng từng dòng."""
        if 'vbs.contact.log' not in self.env:
            return
        ContactLog = self.env['vbs.contact.log']
        for rec in self:
            by_partner = {}
            for line in rec.line_ids:
                if not line.partner_id:
                    continue
                by_partner.setdefault(line.partner_id.id, []).append(line)
            for pid, lines in by_partner.items():
                lines_desc = ', '.join(
                    '%s %sm' % (l.fabric_brand or l.fabric_code or 'vải', l.quantity)
                    for l in lines
                )
                sapo = ', '.join(set(l.sapo_code for l in lines if l.sapo_code))
                ContactLog.sudo().create({
                    'partner_id': pid,
                    'noi_dung': 'Vải đã về — %s (%s)' % (sapo or rec.name, lines_desc),
                    'tinh_trang': 'cho_lien_he',
                })

    def action_reset_draft(self):
        """Reset về DV01 (chỉ admin)."""
        self.write({
            'state': 'draft',
            'date_approved': False,
            'approved_by': False,
        })

    @api.model
    def _get_or_create_daily_draft(self):
        """Trả phiếu DV01 draft của hôm nay, tạo mới nếu chưa có.

        Dùng cho daily aggregation: mọi garment bấm 'Yêu cầu vải' trong ngày
        đều gom vào 1 phiếu DV01 duy nhất.
        """
        today = fields.Date.today()
        order = self.search([
            ('state', '=', 'draft'),
            ('date_order', '=', today),
        ], limit=1)
        if not order:
            order = self.create({'date_order': today})
        return order
