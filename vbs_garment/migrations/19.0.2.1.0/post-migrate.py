# -*- coding: utf-8 -*-
"""Backfill FK links after the Pattern-pivot refactor:

  - vbs_fabric_order_line.garment_id ← match on garment_ref = vbs_garment.ref
  - vbs_garment.fabric_line_id       ← reverse of the above (first match)
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

    if not _col_exists(cr, 'vbs_fabric_order_line', 'garment_id'):
        _logger.info("VBS Garment post-migrate: garment_id column missing, skip")
        return

    # Link fabric_order_line → garment by matching garment_ref text
    cr.execute("""
        UPDATE vbs_fabric_order_line l
        SET garment_id = g.id
        FROM vbs_garment g
        WHERE l.garment_id IS NULL
          AND l.garment_ref IS NOT NULL
          AND l.garment_ref = g.ref
    """)
    linked_lines = cr.rowcount
    _logger.info("VBS Garment post-migrate: linked %d fabric lines to garments", linked_lines)

    # Link garment.fabric_line_id ← first matching line (lowest id)
    cr.execute("""
        UPDATE vbs_garment g
        SET fabric_line_id = sub.line_id
        FROM (
            SELECT DISTINCT ON (garment_id) id AS line_id, garment_id
            FROM vbs_fabric_order_line
            WHERE garment_id IS NOT NULL
            ORDER BY garment_id, id
        ) sub
        WHERE g.id = sub.garment_id
          AND g.fabric_line_id IS NULL
    """)
    linked_garments = cr.rowcount
    _logger.info("VBS Garment post-migrate: linked %d garments to fabric lines", linked_garments)
