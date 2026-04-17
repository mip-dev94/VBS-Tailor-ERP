# -*- coding: utf-8 -*-
"""
Pre-migration: reassign XML IDs from vbs_erp to the new split modules.
This runs BEFORE the module update, so the old XML IDs still exist.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info("VBS ERP migration: reassigning XML IDs to split modules...")

    # ── vbs_base: security groups ──────────────────────────────────────────
    base_names = [
        'module_category_vbs',
        'priv_vbs_admin', 'priv_vbs_accountant', 'priv_vbs_sale',
        'priv_vbs_warehouse', 'priv_vbs_workshop', 'priv_vbs_office',
        'group_vbs_admin', 'group_vbs_accountant', 'group_vbs_sale',
        'group_vbs_warehouse', 'group_vbs_workshop', 'group_vbs_office',
    ]
    _reassign(cr, 'vbs_base', base_names)

    # ── vbs_fabric: fabric models, views, actions, menus, security ─────────
    cr.execute("""
        UPDATE ir_model_data SET module = 'vbs_fabric'
        WHERE module = 'vbs_erp'
          AND (name LIKE '%fabric%' OR name LIKE '%_vbs_fabric_%')
          AND name NOT LIKE '%automation_fabric%'
    """)
    # The fabric automation record
    _reassign(cr, 'vbs_fabric', ['automation_fabric_arrived', 'activity_type_vai_ve'])

    # ── vbs_config: pricing, SLA, pattern, stage template ──────────────────
    cr.execute("""
        UPDATE ir_model_data SET module = 'vbs_config'
        WHERE module = 'vbs_erp'
          AND (name LIKE '%pricing%'
               OR name LIKE '%sla%'
               OR name LIKE '%pattern%'
               OR name LIKE '%stage_template%'
               OR name LIKE '%tmpl_%')
    """)
    _reassign(cr, 'vbs_config', ['seq_vbs_pattern'])

    # ── vbs_garment: garment models, views, actions, menus ─────────────────
    cr.execute("""
        UPDATE ir_model_data SET module = 'vbs_garment'
        WHERE module = 'vbs_erp'
          AND (name LIKE '%garment%'
               OR name LIKE '%planning_slot%'
               OR name LIKE '%sale_order%')
    """)
    _reassign(cr, 'vbs_garment', [
        'seq_vbs_garment',
        'activity_type_lien_he_khach',
        'activity_type_sla_overdue',
        'automation_garment_state_change',
        'ir_cron_vbs_sla_check',
    ])

    # ── vbs_contact: contact log ───────────────────────────────────────────
    cr.execute("""
        UPDATE ir_model_data SET module = 'vbs_contact'
        WHERE module = 'vbs_erp'
          AND name LIKE '%contact%'
    """)

    # ── Menus: reassign to respective modules ──────────────────────────────
    menu_mapping = {
        'vbs_garment': [
            'menu_root_production', 'menu_production_garments', 'menu_production_planning',
        ],
        'vbs_contact': [
            'menu_root_contact', 'menu_contact_orders', 'menu_contact_log',
        ],
        'vbs_hr': [
            'menu_root_employees', 'menu_employees_list',
        ],
        'vbs_fabric': [
            'menu_root_fabric', 'menu_fabric_order', 'menu_fabric_stock', 'menu_fabric_type',
        ],
        'vbs_config': [
            'menu_root_config', 'menu_config_pricing', 'menu_config_sla',
            'menu_config_stage_template', 'menu_config_pattern',
        ],
    }
    for target_module, names in menu_mapping.items():
        _reassign(cr, target_module, names)

    # ── Hide-menus: reassign to vbs_garment ────────────────────────────────
    # These are external IDs that vbs_erp modified (active=False on other modules' menus)
    # They don't need reassignment since they reference other modules' XML IDs

    _logger.info("VBS ERP migration: XML ID reassignment complete.")


def _reassign(cr, target_module, names):
    """Reassign specific XML IDs from vbs_erp to target_module."""
    if not names:
        return
    placeholders = ', '.join(['%s'] * len(names))
    cr.execute(f"""
        UPDATE ir_model_data
        SET module = %s
        WHERE module = 'vbs_erp'
          AND name IN ({placeholders})
    """, [target_module] + names)
    count = cr.rowcount
    if count:
        _logger.info("  Reassigned %d XML IDs to %s", count, target_module)
