# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

{
    'name': "Inventory/Stock Aging Report",
    'version': "16.0.0.0",
    'summary': "The stock aging analysis report helps you to analyze the age of your stock by organizing the value and quantity into periods.",
    'category': 'Warehouse',
    'description': """
    Analysis report for your stock
    stock analysis report
    period wise analysis of stock
    analyze the age of the stock
    period wise stock analysis report
    stock aging report
    inventory aging
    analyze inventory stock
    analysis inventory stock
    stock evaluation
    inventory evaluation
    track quick moving stock
    track slow moving stock
    track fast moving stock
    stock by organizing the value and quantity
    stock by organizing the value and quantity into periods
    stock report
    inventory stock report
    track incoming and outgoing stock
    track period wise
    track date wise stock
    tack date wise inventory
    check periodically stock inventory
    track not moving stock
    track future stock levels
    stock.move report
    aging report by warehouse
    aging report by location
    product category aging report
    manually selection product for stock aging report
    """,
    'author': "Sitaram",
    'website':"www.sitaramsolutions.in",
    'depends': ['base','stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sr_stock_aging_report.xml',
        'report/report.xml',
        'report/sr_stock_aging_report_template.xml'
    ],
    'demo': [],
    "external_dependencies": {},
    "license": "OPL-1",
    'installable': True,
    'auto_install': False,
    "price": 20,
    "currency": 'EUR',
    'live_test_url':'https://youtu.be/8BVmio9ag-g',
    'images': ['static/description/banner.png'],
}
