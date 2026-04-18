# -*- coding: utf-8 -*-
"""Bỏ field `confirmed_cs` khi rút triple confirmation còn 2 (Sale + QA)."""


def migrate(cr, version):
    cr.execute("""
        ALTER TABLE vbs_garment
        DROP COLUMN IF EXISTS confirmed_cs
    """)
    cr.execute("""
        DELETE FROM ir_model_fields
        WHERE model = 'vbs.garment' AND name = 'confirmed_cs'
    """)
