# -*- coding: utf-8 -*-
{
    'name': "Asset and Meeting Room Management",

    'summary': """
        Manage meeting rooms and assets integrated with HR.
    """,

    'description': """
        Module for managing company assets and meeting rooms.
        - Room booking
        - Asset tracking
        - Maintenance history
        - HR integration
        - AI-powered room recommendation
    """,

    'author': "Antigravity",
    'website': "http://www.yourcompany.com",

    'category': 'Management',
    'version': '1.1',

    'depends': ['base', 'nhan_su'],

    'data': [
        'security/ir.model.access.csv',
        'views/meeting_room_views.xml',
        'views/asset_management_views.xml',
        'views/room_booking_views.xml',
        'views/ai_assistant_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'asset_meeting_room/static/src/js/ai_assistant.js',
        ],
    },
    'application': True,
}
