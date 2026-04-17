# -*- coding: utf-8 -*-
{
    'name': 'VBS Liên hệ khách hàng',
    'version': '19.0.1.0.0',
    'category': 'VBS',
    'summary': 'Nhật ký liên hệ khách hàng',
    'description': 'Quản lý nhật ký liên hệ khách hàng VBS.',
    'depends': ['vbs_base', 'vbs_garment', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/vbs_contact_log_views.xml',
        'views/vbs_contact_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
