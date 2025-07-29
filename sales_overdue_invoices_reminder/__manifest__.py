{
    'name': 'Sales Overdue Invoices Reminder',
    'version': '1.0',
    'description': 'Sends email notifications every 3 days to salespersons about their overdue invoices.',
    'summary': 'Automatically notifies salespersons of their overdue invoices',
    'author': 'Joff Pascual',
    'website': 'https://joffpascual.odoo.com',
    'depends': [
        'accountant', 'sales_management'
    ],
    'data': [
        'data/cron.xml',
    ],
    'installable' : True,
    'application' : False,
    'auto_install' : False,
        
}