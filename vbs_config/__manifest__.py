# -*- coding: utf-8 -*-
{
    'name': 'VBS Cấu hình',
    'version': '19.0.1.3.0',
    'depends': ['vbs_base', 'vbs_fabric', 'mail'],
    'category': 'VBS',
    'summary': 'Bảng giá, SLA, template công đoạn, mã rập',
    'description': 'Quản lý cấu hình sản xuất VBS: giá gia công, SLA, template công đoạn, mã rập.',
    'data': [
        'security/ir.model.access.csv',
        'data/currency_setup.xml',
        'data/vbs_sequence_data.xml',
        'data/vbs_stage_template_data.xml',
        'views/vbs_pricing_views.xml',
        'views/vbs_sla_config_views.xml',
        'views/vbs_stage_template_views.xml',
        'views/vbs_pattern_views.xml',
        'views/res_config_settings_views.xml',
        'views/vbs_config_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
