# -*- coding: utf-8 -*-
"""Rename vbs_fabric_stock.quantity_available -> quantity_received.

Old field stored on-hand balance directly. New model splits:
  quantity_received (stored, from DV04 arrivals)
  quantity_consumed (computed in vbs_garment, from garment.fabric_meters)
  quantity_available (computed in vbs_garment, = received - consumed)
Backfill assumes existing balances were all "received and not yet consumed".
"""
import logging

_logger = logging.getLogger(__name__)


def _col_exists(cr, table, col):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table, col))
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return

    has_old = _col_exists(cr, 'vbs_fabric_stock', 'quantity_available')
    has_new = _col_exists(cr, 'vbs_fabric_stock', 'quantity_received')

    if has_old and not has_new:
        cr.execute(
            "ALTER TABLE vbs_fabric_stock "
            "RENAME COLUMN quantity_available TO quantity_received"
        )
        _logger.info("VBS Fabric 1.3: renamed quantity_available -> quantity_received")
    elif has_old and has_new:
        # Merge: copy old into new where new is 0/NULL, then drop old
        cr.execute("""
            UPDATE vbs_fabric_stock
            SET quantity_received = quantity_available
            WHERE (quantity_received IS NULL OR quantity_received = 0)
              AND quantity_available IS NOT NULL
        """)
        cr.execute("ALTER TABLE vbs_fabric_stock DROP COLUMN quantity_available")
        _logger.info("VBS Fabric 1.3: merged quantity_available into quantity_received")
    else:
        _logger.info("VBS Fabric 1.3: no rename needed")
