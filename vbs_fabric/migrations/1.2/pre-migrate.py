# -*- coding: utf-8 -*-
"""Backfill partner/branch/sapo/garment_ref/inspection_state from header to lines,
then drop those columns from vbs_fabric_order."""
import logging

_logger = logging.getLogger(__name__)


HEADER_COLS = ('partner_id', 'branch', 'sapo_code', 'garment_ref', 'inspection_state')


def _col_exists(cr, table, col):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table, col))
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return

    # Ensure name column on header; backfill from sapo_code or ID
    if not _col_exists(cr, 'vbs_fabric_order', 'name'):
        cr.execute("ALTER TABLE vbs_fabric_order ADD COLUMN name VARCHAR")
        _logger.info("VBS Fabric: added vbs_fabric_order.name")
    if _col_exists(cr, 'vbs_fabric_order', 'sapo_code'):
        cr.execute("""
            UPDATE vbs_fabric_order
            SET name = COALESCE(sapo_code, 'DV-' || id)
            WHERE name IS NULL OR name = ''
        """)
    else:
        cr.execute("""
            UPDATE vbs_fabric_order
            SET name = 'DV-' || id
            WHERE name IS NULL OR name = ''
        """)

    # Only backfill if the old header columns still exist
    present = [c for c in HEADER_COLS if _col_exists(cr, 'vbs_fabric_order', c)]
    if not present:
        _logger.info("VBS Fabric: header columns already removed, skipping backfill")
        return

    # Ensure line columns exist (ORM will add them in update, but we need them before UPDATE)
    for col, ddl in [
        ('partner_id', 'INTEGER'),
        ('branch', 'VARCHAR'),
        ('sapo_code', 'VARCHAR'),
        ('garment_ref', 'VARCHAR'),
        ('inspection_state', 'VARCHAR'),
    ]:
        if not _col_exists(cr, 'vbs_fabric_order_line', col):
            cr.execute(
                "ALTER TABLE vbs_fabric_order_line ADD COLUMN %s %s" % (col, ddl)
            )
            _logger.info("VBS Fabric: added column vbs_fabric_order_line.%s", col)

    # Backfill line values from header where line value is NULL
    set_clauses = []
    for c in present:
        set_clauses.append(f"{c} = COALESCE(l.{c}, o.{c})")
    set_sql = ', '.join(set_clauses)
    cr.execute(f"""
        UPDATE vbs_fabric_order_line l
        SET {set_sql}
        FROM vbs_fabric_order o
        WHERE l.order_id = o.id
    """)
    _logger.info("VBS Fabric: backfilled %d line records from header", cr.rowcount)

    # Set sensible defaults for lines without an order match
    cr.execute("""
        UPDATE vbs_fabric_order_line
        SET branch = COALESCE(branch, 'vbs_hn'),
            inspection_state = COALESCE(inspection_state, 'chua_kt')
    """)

    # For lines that still have NULL partner_id, assign a placeholder partner
    # (required=True will fail otherwise). Use the first available partner as fallback.
    cr.execute("SELECT id FROM res_partner ORDER BY id LIMIT 1")
    row = cr.fetchone()
    if row:
        cr.execute("""
            UPDATE vbs_fabric_order_line
            SET partner_id = %s
            WHERE partner_id IS NULL
        """, (row[0],))
        if cr.rowcount:
            _logger.warning(
                "VBS Fabric: assigned placeholder partner %s to %d orphan lines",
                row[0], cr.rowcount,
            )
