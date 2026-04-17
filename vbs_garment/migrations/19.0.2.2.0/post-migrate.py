# -*- coding: utf-8 -*-
"""
Cleanup obsolete records:
  - Gap #3: inert base.automation `automation_garment_state_change` (both vbs_garment + vbs_erp copies)
  - Gap #5: 4 dashboard actions + 4 submenus + 1 separator menu
"""


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})

    xml_ids = [
        # Gap #3
        'vbs_garment.automation_garment_state_change',
        'vbs_erp.automation_garment_state_change',
        # Gap #5 — actions
        'vbs_garment.action_garment_ready_vp',
        'vbs_garment.action_garment_fitting',
        'vbs_garment.action_garment_done',
        'vbs_garment.action_garment_overdue',
        # Gap #5 — menus
        'vbs_garment.menu_garment_ready_vp',
        'vbs_garment.menu_garment_fitting',
        'vbs_garment.menu_garment_done',
        'vbs_garment.menu_garment_overdue',
        'vbs_garment.menu_dashboard_sep',
    ]
    for xid in xml_ids:
        rec = env.ref(xid, raise_if_not_found=False)
        if rec:
            rec.unlink()
