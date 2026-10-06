{
    'name': 'Stock Ageing Report',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'FIFO-based product ageing per stock location (pivot report)',
    'description': """
Ageing Products report under Inventory > Reporting.

* Ageing starts when stock enters the warehouse stock location.
* FIFO layers per product/location, bucketed in 0-30 / 30-90 / 90-180 / 180-365 / 365+ days.
* Products that were never sold are aged at 365 days.
* Returns restart at 0 days.
* Consignment locations are excluded.
""",
    # Only the Inventory app is required.
    'depends': ['stock'],
    # Files are loaded in this order: security first, then views/actions/menus.
    'data': [
        'security/ir.model.access.csv',        # who can read the report model
        'security/security.xml',               # multi-company record rule
        'views/stock_location_views.xml',      # "Consignment" checkbox on locations
        'views/stock_ageing_report_views.xml', # pivot / list / search views
        'views/stock_ageing_wizard_views.xml', # options window, menu entry, nightly cron
        'views/stock_ageing_report_templates.xml',  # PDF layout
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
