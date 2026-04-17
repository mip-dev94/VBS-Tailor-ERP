# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ── SLA defaults ────────────────────────────────────────────────────
    vbs_sla_default_days = fields.Integer(
        string='SLA mặc định (ngày)',
        config_parameter='vbs.sla_default_days',
        default=7,
        help='Số ngày SLA mặc định cho công đoạn mới.',
    )

    # ── CRM Automation toggles ──────────────────────────────────────────
    vbs_auto_contact_log = fields.Boolean(
        string='Tự động tạo Contact Log',
        config_parameter='vbs.auto_contact_log',
        default=True,
        help='Tự động tạo ghi chú liên hệ khi trạng thái đồ hoặc vải thay đổi.',
    )
    vbs_auto_notify_sale = fields.Boolean(
        string='Thông báo Sale khi đồ về VP',
        config_parameter='vbs.auto_notify_sale',
        default=True,
        help='Tự tạo activity cho Sale khi đồ chuyển về văn phòng.',
    )
    vbs_fitting_reminder = fields.Boolean(
        string='Nhắc thử đồ',
        config_parameter='vbs.fitting_reminder',
        default=True,
        help='Cron hàng ngày nhắc nhở khách thử đồ đang chờ.',
    )

    # ── Company defaults ────────────────────────────────────────────────
    vbs_company_phone = fields.Char(
        related='company_id.phone', readonly=False,
        string='SĐT cửa hàng',
    )
    vbs_company_email = fields.Char(
        related='company_id.email', readonly=False,
        string='Email cửa hàng',
    )
    vbs_company_street = fields.Char(
        related='company_id.street', readonly=False,
        string='Địa chỉ',
    )
