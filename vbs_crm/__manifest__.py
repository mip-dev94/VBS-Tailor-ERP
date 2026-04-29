# -*- coding: utf-8 -*-
{
    'name': 'VBS CRM',
    'version': '19.0.1.0.0',
    'category': 'VBS',
    'sequence': 10,
    'author': 'VBS',
    'summary': 'Quản lý lead, cơ hội bán hàng và contact list khách hàng',
    'depends': ['vbs_base', 'vbs_garment', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/vbs_crm_lead_views.xml',
        'views/vbs_crm_partner_views.xml',
        'views/vbs_crm_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
