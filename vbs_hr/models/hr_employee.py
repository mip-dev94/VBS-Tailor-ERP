# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ── VBS Role booleans (computed + inverse) ───────────────────────────────
    vbs_role_admin = fields.Boolean(
        string='Quản trị VBS',
        compute='_compute_vbs_roles', inverse='_inverse_vbs_roles', store=False,
    )
    vbs_role_accountant = fields.Boolean(
        string='Kế toán VBS',
        compute='_compute_vbs_roles', inverse='_inverse_vbs_roles', store=False,
    )
    vbs_role_sale = fields.Boolean(
        string='Sale VBS',
        compute='_compute_vbs_roles', inverse='_inverse_vbs_roles', store=False,
    )
    vbs_role_warehouse = fields.Boolean(
        string='Kho VBS',
        compute='_compute_vbs_roles', inverse='_inverse_vbs_roles', store=False,
    )
    vbs_role_workshop = fields.Boolean(
        string='Xưởng VBS',
        compute='_compute_vbs_roles', inverse='_inverse_vbs_roles', store=False,
    )
    vbs_role_office = fields.Boolean(
        string='Văn phòng VBS',
        compute='_compute_vbs_roles', inverse='_inverse_vbs_roles', store=False,
    )

    vbs_role_display = fields.Char(
        string='Vai trò VBS',
        compute='_compute_vbs_role_display',
    )

    def _get_vbs_group_map(self):
        """Map field name → XML ID."""
        return {
            'vbs_role_admin': 'vbs_base.group_vbs_admin',
            'vbs_role_accountant': 'vbs_base.group_vbs_accountant',
            'vbs_role_sale': 'vbs_base.group_vbs_sale',
            'vbs_role_warehouse': 'vbs_base.group_vbs_warehouse',
            'vbs_role_workshop': 'vbs_base.group_vbs_workshop',
            'vbs_role_office': 'vbs_base.group_vbs_office',
        }

    @api.depends('user_id', 'user_id.group_ids')
    def _compute_vbs_roles(self):
        group_map = self._get_vbs_group_map()
        groups = {}
        for field_name, xmlid in group_map.items():
            groups[field_name] = self.env.ref(xmlid, raise_if_not_found=False)

        for emp in self:
            user = emp.user_id
            if not user:
                for field_name in group_map:
                    emp[field_name] = False
                continue
            user_groups = user.group_ids
            for field_name, group in groups.items():
                emp[field_name] = bool(group and group in user_groups)

    def _inverse_vbs_roles(self):
        group_map = self._get_vbs_group_map()
        groups = {}
        for field_name, xmlid in group_map.items():
            groups[field_name] = self.env.ref(xmlid, raise_if_not_found=False)

        for emp in self:
            if not emp.user_id:
                continue
            user = emp.user_id.sudo()
            for field_name, group in groups.items():
                if not group:
                    continue
                current = group in user.group_ids
                desired = emp[field_name]
                if desired and not current:
                    user.write({'group_ids': [(4, group.id)]})
                elif not desired and current:
                    user.write({'group_ids': [(3, group.id)]})

    @api.depends('user_id', 'user_id.group_ids')
    def _compute_vbs_role_display(self):
        group_map = self._get_vbs_group_map()
        label_map = {
            'vbs_role_admin': 'Admin',
            'vbs_role_accountant': 'Kế toán',
            'vbs_role_sale': 'Sale',
            'vbs_role_warehouse': 'Kho',
            'vbs_role_workshop': 'Xưởng',
            'vbs_role_office': 'VP',
        }
        groups = {}
        for field_name, xmlid in group_map.items():
            groups[field_name] = self.env.ref(xmlid, raise_if_not_found=False)

        for emp in self:
            if not emp.user_id:
                emp.vbs_role_display = ''
                continue
            user_groups = emp.user_id.group_ids
            roles = [
                label_map[fn]
                for fn, g in groups.items()
                if g and g in user_groups
            ]
            emp.vbs_role_display = ', '.join(roles) if roles else 'Chưa phân quyền'
