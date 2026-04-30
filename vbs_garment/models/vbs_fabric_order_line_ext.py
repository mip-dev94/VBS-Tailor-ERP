# -*- coding: utf-8 -*-
"""Extend vbs.fabric.order.line with garment_id FK + pattern pivot + arrival hook.

Lives in vbs_garment (depends on vbs_fabric) to avoid circular dep.
"""
from odoo import _, api, fields, models


# Map garment_type selection → fabric line garment_desc selection
_GARMENT_DESC_MAP = {
    'so_mi': 'so_mi',
    'ao_khoac_le': 'ao_khoac_le',
    'quan_le': 'quan_le',
    'bo_comple_2': 'bo_comple_2',
    'bo_comple_3': 'bo_comple_3',
    'gile': 'gile',
    'ao_khoac_tao_kieu': 'ao_khoac_tao_kieu',
}


class VbsFabricOrderLineExt(models.Model):
    _inherit = 'vbs.fabric.order.line'

    # M2O links lên Sale (data hub) — thay thế sapo_code Char
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Đơn hàng',
        ondelete='set null',
        index=True,
        help='Đơn hàng yêu cầu đặt vải này.',
    )
    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Dòng đơn',
        ondelete='set null',
        index=True,
        help='Dòng cụ thể trong đơn hàng.',
    )

    garment_id = fields.Many2one(
        'vbs.garment',
        string='Đồ may',
        ondelete='set null',
        index=True,
        help='Đồ may mà dòng vải này phục vụ',
    )

    pattern_id = fields.Many2one(
        'vbs.pattern',
        string='Mã rập',
        related='garment_id.pattern_id',
        store=True,
        index=True,
    )

    def _after_line_arrived(self):
        """Bump fabric stock và tạo activity cho garment phụ trách khi dòng vải về."""
        super()._after_line_arrived()
        Stock = self.env['vbs.fabric.stock']
        activity_type = self.env.ref(
            'vbs_garment.activity_type_lien_he_khach', raise_if_not_found=False,
        )
        for line in self:
            if line.partner_id and line.fabric_type_id and line.quantity:
                stock = Stock.search([
                    ('partner_id', '=', line.partner_id.id),
                    ('fabric_type_id', '=', line.fabric_type_id.id),
                ], limit=1)
                if stock:
                    stock.quantity_received = (stock.quantity_received or 0.0) + line.quantity
                else:
                    Stock.create({
                        'partner_id': line.partner_id.id,
                        'fabric_type_id': line.fabric_type_id.id,
                        'fabric_order_id': line.order_id.id,
                        'fabric_brand': line.fabric_brand or (line.fabric_type_id.fabric_brand or ''),
                        'fabric_type': line.fabric_type_id.name,
                        'quantity_received': line.quantity,
                        'note': _('Nhập từ %s') % line.order_id.name,
                    })
            garment = line.garment_id
            if garment and garment.responsible_id and activity_type:
                garment.activity_schedule(
                    activity_type_id=activity_type.id,
                    summary=_('Vải đã về — có thể bắt đầu cắt đồ %s') % (
                        garment.ref or garment.name,
                    ),
                    user_id=garment.responsible_id.id,
                )

    @api.onchange('garment_id')
    def _onchange_garment_id(self):
        g = self.garment_id
        if not g:
            return
        if g.partner_id:
            self.partner_id = g.partner_id
        # Link M2O lên sale
        if g.order_id and not self.sale_order_id:
            self.sale_order_id = g.order_id
        if g.order_line_id and not self.sale_order_line_id:
            self.sale_order_line_id = g.order_line_id
        # Giữ sapo_code Char cho legacy
        if g.order_id and not self.sapo_code:
            self.sapo_code = g.order_id.name
        if g.ref and not self.garment_ref:
            self.garment_ref = g.ref
        if g.garment_type and not self.garment_desc:
            self.garment_desc = _GARMENT_DESC_MAP.get(g.garment_type)
        if g.fabric_id and not self.fabric_type_id:
            self.fabric_type_id = g.fabric_id
            if not self.fabric_brand:
                self.fabric_brand = g.fabric_id.fabric_brand
            if not self.fabric_code:
                self.fabric_code = g.fabric_id.code
        if g.fabric_meters and not self.quantity:
            self.quantity = g.fabric_meters

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        """Khi chọn đơn hàng → auto-fill khách + sapo_code legacy."""
        if self.sale_order_id:
            if not self.partner_id and self.sale_order_id.partner_id:
                self.partner_id = self.sale_order_id.partner_id
            if not self.sapo_code:
                self.sapo_code = self.sale_order_id.name
