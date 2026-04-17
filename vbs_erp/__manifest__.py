# -*- coding: utf-8 -*-
{
    'name': 'VBS ERP (Bridge)',
    'version': '19.0.2.0.0',
    'category': 'VBS',
    'summary': 'Bridge module — sẽ bị xoá sau khi migration hoàn tất',
    'description': 'Hollow wrapper that depends on all split VBS modules. '
                   'Safe to uninstall after verifying the split modules work correctly.',
    'depends': [
        'vbs_base',
        'vbs_fabric',
        'vbs_config',
        'vbs_garment',
        'vbs_contact',
        'vbs_hr',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
