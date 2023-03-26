# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import api, fields, models, _
from datetime import datetime
import time
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class srStockAgingReport(models.TransientModel):
    _name = 'sr.stock.aging.report'
    _description = 'Stock Aging Report'

    date_from = fields.Date('Start Date', default=lambda *a: time.strftime('%Y-%m-%d'))
    result_selection = fields.Selection([('product', 'Product'), ('category', 'Category')], default='product', string='Filter By')
    product_categ_ids = fields.Many2many('product.category', string="Category")
    product_ids = fields.Many2many('product.product', string="Product")
    company_id = fields.Many2one('res.company', 'Company')
    period_length = fields.Integer('Period Length (Days)', default=30)
    target_result = fields.Selection([('warehouse', 'Warehouse'), ('location', 'Location')], default='warehouse', string='Report Based on')
    location_ids = fields.Many2many('stock.location', string="Location")
    warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouse")
    
    def print_stock_inventory_aging(self):
        res = {}
        data = {}
        if self.period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        start = self.date_from.strftime("%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = datetime.strptime(start, "%Y-%m-%d") - relativedelta(days=self.period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (str((5 - (i + 1)) * self.period_length) + '-' + str((5 - i) * self.period_length)) or ('+' + str(4 * self.period_length))),
                'stop': start,
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = (stop - relativedelta(days=1)).strftime("%Y-%m-%d")
        data = {
            'column':res,
            'warehouse':self.warehouse_ids.ids,
            'location':self.location_ids.ids,
            'date_from':self.date_from,
            'result_selection':self.result_selection,
            'product_categ_ids':self.product_categ_ids.ids,
            'product_ids':self.product_ids.ids,
            'company_id':self.company_id.id,
            'period_length':self.period_length,
            'target_result':self.target_result,
            'is_warehouse': True if self.target_result == 'warehouse' else False,
            'is_location': True if self.target_result == 'location' else False,
            }
        return self.env.ref('sr_stock_aging_report.action_report_stock_aging').report_action(self, data=data)

