# -*- coding: utf-8 -*-
{
    'name': 'VBS Sản phẩm B2C',
    'version': '19.0.1.2.0',
    'category': 'VBS',
    'sequence': 15,
    'author': 'VBS',
    'summary': 'Quản lý sản phẩm B2C thành phẩm: catalog, tồn kho theo cửa hàng',
    'depends': ['vbs_base', 'vbs_fabric', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/vbs_product_sequence.xml',
        'views/vbs_product_views.xml',
        'views/vbs_product_stock_views.xml',
        'views/vbs_product_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
