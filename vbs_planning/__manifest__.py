# -*- coding: utf-8 -*-
{
    'name': 'VBS Planning',
    'version': '1.0',
    'category': 'VBS',
    'sequence': 60,
    'author': 'VBS',
    'summary': 'Lập lịch ca làm việc cho nhân viên',
    'description': """
        Module quản lý lịch làm việc và ca trực cho nhân viên.
        - Tạo và phân công ca làm việc
        - Xem lịch theo tuần/tháng
        - Quản lý theo phòng ban và dự án
    """,
    'depends': ['hr', 'resource', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/planning_data.xml',
        'views/planning_slot_views.xml',
        'views/planning_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
