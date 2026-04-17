# -*- coding: utf-8 -*-
"""Migrate fabric order states: chua_ve → cho_ve, da_ve stays da_ve."""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info("VBS Fabric: migrating fabric order states to DV01-DV04")
    # chua_ve → cho_ve (DV03: chờ vải về — closest equivalent)
    cr.execute("""
        UPDATE vbs_fabric_order
        SET state = 'cho_ve'
        WHERE state = 'chua_ve'
    """)
    _logger.info("VBS Fabric: migrated %d records from chua_ve → cho_ve", cr.rowcount)
