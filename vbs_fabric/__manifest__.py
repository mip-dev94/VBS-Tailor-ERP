# -*- coding: utf-8 -*-
{
    'name': 'VBS Fabric',
    'version': '1.6',
    'category': 'VBS',
    'sequence': 14,
    'author': 'VBS',
    'summary': 'Quản lý vải: danh mục, đặt hàng, tồn kho',
    'depends': ['vbs_base', 'mail', 'base_automation'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'data/ir_sequence_data.xml',
        'data/mail_activity_type_data.xml',
        'views/vbs_fabric_type_views.xml',
        'views/vbs_fabric_order_views.xml',
        'views/vbs_fabric_stock_views.xml',
        'views/vbs_fabric_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
