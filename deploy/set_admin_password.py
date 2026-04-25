#!/usr/bin/env python3
"""Reset Odoo admin password. Đọc password từ env NEW_PASSWORD."""
import os
import sys

sys.argv = ['odoo', '-c', '/etc/odoo/odoo.conf']
import odoo  # noqa: E402
from odoo.tools import config  # noqa: E402
config.parse_config(sys.argv[1:])

from odoo.modules.registry import Registry  # noqa: E402

new_pw = os.environ.get('NEW_PASSWORD', '')
if len(new_pw) < 8:
    print('ERROR: Password phải có ít nhất 8 ký tự')
    sys.exit(1)

registry = Registry('VBS_ERP')
with registry.cursor() as cr:
    from odoo import api, SUPERUSER_ID  # noqa: E402
    env = api.Environment(cr, SUPERUSER_ID, {})
    Users = env['res.users']
    hashed = Users._crypt_context().hash(new_pw)
    Users._set_encrypted_password(2, hashed)
    admin = env['res.users'].browse(2)
    cr.commit()
    print(f'OK: Password của [{admin.login}] đã được đặt thành công')
