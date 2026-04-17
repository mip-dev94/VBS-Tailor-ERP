# -*- coding: utf-8 -*-
"""Extend vbs.fabric.order arrival flow: notify garment responsible + bump stock.

Lives in vbs_garment (depends on vbs_fabric) so we can reference vbs.garment
and vbs.fabric.stock from here without creating a circular dep.
"""
from odoo import _, api, fields, models


class VbsFabricOrderExt(models.Model):
    _inherit = 'vbs.fabric.order'

    def action_mark_arrived(self):
        result = super().action_mark_arrived()
        for rec in self:
            rec._bump_fabric_stock_received()
            rec._notify_garments_fabric_arrived()
        return result

    def _bump_fabric_stock_received(self):
        """Cộng line.quantity vào stock.quantity_received; tạo mới nếu chưa có."""
        Stock = self.env['vbs.fabric.stock']
        for line in self.line_ids:
            if not line.partner_id or not line.fabric_type_id or not line.quantity:
                continue
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
                    'fabric_order_id': self.id,
                    'fabric_brand': line.fabric_brand or (line.fabric_type_id.fabric_brand or ''),
                    'fabric_type': line.fabric_type_id.name,
                    'quantity_received': line.quantity,
                    'note': _('Nhập từ %s') % self.name,
                })

    def _notify_garments_fabric_arrived(self):
        """Tạo activity cho người phụ trách garment: 'Vải về, bắt đầu cắt'."""
        activity_type = self.env.ref(
            'vbs_garment.activity_type_lien_he_khach', raise_if_not_found=False,
        )
        for line in self.line_ids:
            garment = line.garment_id
            if not garment or not garment.responsible_id:
                continue
            if not activity_type:
                continue
            garment.activity_schedule(
                activity_type_id=activity_type.id,
                summary=_('Vải đã về — có thể bắt đầu cắt đồ %s') % (
                    garment.ref or garment.name,
                ),
                user_id=garment.responsible_id.id,
            )
