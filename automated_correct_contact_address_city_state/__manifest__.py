{
    'name': 'Automated Correct Contact Address (Region, City, State)',
    'version': '19.0.1.0.0',
    'description': 'Scans the contact address and automatically fills in the Region, City and State.',
    'summary': 'Auto-fill Region, City and State from the contact address',
    'author': 'Jofferson Pascual',
    'website': '',
    'license': 'LGPL-3',
    'category': 'Contacts',
    'depends': [
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_country_region_views.xml',
        'views/res_partner_views.xml',
        'data/ir_cron_data.xml',
        'data/res_country_city_data.xml',
    ],
    'post_init_hook': '_post_init_link_regions',
    'auto_install': False,
    'application': False,
}
