# -*- coding: utf-8 -*-
{
    'name': "Project Extension",

    'summary': """
        Add notifications to project module""",

    'description': """
        Add notifications to project module
    """,

    'author': "Olalekan Babawale",
    'website': "http://obabawale.github.io",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'project'],

    'data': [
        'data/email_data.xml',
        'data/ir_cron.xml',
    ],
    'license': 'LGPL-3',
}
