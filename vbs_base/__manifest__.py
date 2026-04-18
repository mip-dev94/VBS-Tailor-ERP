# -*- coding: utf-8 -*-
{
    'name': 'VBS Base',
    'version': '1.0',
    'category': 'VBS',
    'sequence': 5,
    'author': 'VBS',
    'summary': 'Constants và phân quyền dùng chung cho tất cả module VBS',
    'depends': ['base'],
    'data': [
        'security/res_groups.xml',
        'data/menu_overrides.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
