# -*- coding: utf-8 -*-
{
    'name': 'VBS Kế toán',
    'version': '19.0.1.0.0',
    'category': 'VBS',
    'sequence': 14,
    'author': 'VBS',
    'summary': 'Doanh thu, công nợ và theo dõi chi phí cho tiệm may (kế toán nhẹ)',
    'depends': ['vbs_base', 'vbs_garment', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/vbs_expense_views.xml',
        'views/vbs_revenue_views.xml',
        'views/vbs_receivable_views.xml',
        'views/vbs_accounting_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
