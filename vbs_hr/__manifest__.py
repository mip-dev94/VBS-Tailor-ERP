# -*- coding: utf-8 -*-
{
    'name': 'VBS Nhân viên',
    'version': '19.0.1.1.0',
    'category': 'VBS',
    'summary': 'Menu nhân viên VBS',
    'description': 'Menu quản lý nhân viên dành cho VBS admin.',
    'depends': ['vbs_base', 'hr'],
    'data': [
        'views/vbs_hr_menus.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
