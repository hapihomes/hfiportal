{
    'name': 'Dispatch Delivery Receipt',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Delivery',
    'summary': 'Dispatch Delivery Receipt (DDR) sheet populated from delivery orders and Fleet',
    'depends': ['stock', 'sale_stock', 'fleet', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'report/dispatch_receipt_report.xml',
        'views/dispatch_receipt_views.xml',
        'views/stock_picking_views.xml',
    ],
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
}
