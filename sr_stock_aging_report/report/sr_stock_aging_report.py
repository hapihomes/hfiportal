# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import models, api
from datetime import datetime, timedelta


class StockAgingReport(models.AbstractModel):
    _name = 'report.sr_stock_aging_report.report_stock_aging'

    def _find_outgoing_qty(self, product_id, warehouse_id, start_date, end_date, company_id):
        end_date = end_date+" 23:59:59"
        if start_date:
            date_start = start_date+" 00:00:00"
        else:
            date_start = start_date

        if not start_date:
            self._cr.execute('''
            SELECT
                SUM(product_uom_qty) AS qty
            FROM stock_move
            WHERE product_id = %s
            AND date<=%s
            AND state='done'
            AND company_id=%s
            AND location_dest_id in (select id from stock_location where usage='customer')
        ''', (product_id, end_date, company_id.id))
        else:
            self._cr.execute('''
	            SELECT
	                SUM(product_uom_qty) AS qty
	            FROM stock_move
	            WHERE product_id = %s
	            AND date>=%s
	            AND date<=%s
	            AND state='done'
	            AND company_id=%s
                AND location_dest_id in (select id from stock_location where usage='customer')
	        ''', (product_id, date_start, end_date, company_id.id))
        query_res = self._cr.dictfetchall()[0]
        if query_res.get('qty') == None:
            return 0
        else:
            return query_res.get('qty')

    def _find_incoming_qty(self, product_id, warehouse_id, start_date, end_date, company_id):
        end_date = end_date+" 23:59:59"
        if start_date:
            date_start = start_date+" 00:00:00"
        else:
            date_start = start_date
        if not start_date:
            self._cr.execute('''
            SELECT
                SUM(product_uom_qty) AS qty
            FROM stock_move
            WHERE product_id = %s
            AND date<=%s
            AND state='done'
            AND company_id=%s
            AND location_id in (select id from stock_location where usage='supplier')
        ''', (product_id, end_date, company_id.id))
        else:
            self._cr.execute('''
	            SELECT
	                SUM(product_uom_qty) AS qty
	            FROM stock_move
	            WHERE product_id = %s
	            AND date>=%s
	            AND date<=%s
	            AND state='done'
	            AND company_id=%s
                AND location_id in (select id from stock_location where usage='supplier')
	        ''', (product_id, date_start, end_date, company_id.id))

        query_res = self._cr.dictfetchall()[0]
        if query_res.get('qty') == None:
            return 0
        else:
            return query_res.get('qty')

    def _find_inventory_qty(self, product_id, warehouse_id, start_date, end_date, company_id):
        end_date = end_date+" 23:59:59"
        if start_date:
            date_start = start_date+" 00:00:00"
        else:
            date_start = start_date
        if not start_date:
            self._cr.execute('''
            SELECT
                SUM(product_uom_qty) AS qty
            FROM stock_move
            WHERE product_id = %s
            AND date<=%s
            AND state='done'
            AND company_id=%s
            AND location_id in (select id from stock_location where usage='inventory')
        ''', (product_id, end_date, company_id.id))
        else:
            self._cr.execute('''
	            SELECT
	                SUM(product_uom_qty) AS qty
	            FROM stock_move
	            WHERE product_id = %s
	            AND date>=%s
	            AND date<=%s
	            AND state='done'
	            AND company_id=%s
                AND location_id in (select id from stock_location where usage='inventory')
	        ''', (product_id, date_start, end_date, company_id.id))

        query_res = self._cr.dictfetchall()[0]
        if query_res.get('qty') == None:
            return 0
        else:
            return query_res.get('qty')

    def _find_inventory_return_qty(self, product_id, warehouse_id, start_date, end_date, company_id):
        end_date = end_date+" 23:59:59"
        if start_date:
            date_start = start_date+" 00:00:00"
        else:
            date_start = start_date
        if not start_date:
            self._cr.execute('''
            SELECT
                SUM(product_uom_qty) AS qty
            FROM stock_move
            WHERE product_id = %s
            AND date<=%s
            AND state='done'
            AND company_id=%s
            AND location_id in (select id from stock_location where usage='customer')
        ''', (product_id, end_date, company_id.id))
        else:
            self._cr.execute('''
	            SELECT
	                SUM(product_uom_qty) AS qty
	            FROM stock_move
	            WHERE product_id = %s
	            AND date>=%s
	            AND date<=%s
	            AND state='done'
	            AND company_id=%s
                AND location_id in (select id from stock_location where usage='customer')
	        ''', (product_id, date_start, end_date, company_id.id))

        query_res = self._cr.dictfetchall()[0]
        if query_res.get('qty') == None:
            return 0
        else:
            return query_res.get('qty')

    def _find_internal_qty(self, product_id, warehouse_id, start_date, end_date, company_id):
        end_date = end_date+" 23:59:59"
        if start_date:
            date_start = start_date+" 00:00:00"
        else:
            date_start = start_date
        
        domain = [
            ('product_id', '=', product_id),
            ('date', '>=', date_start),
            ('date', '<=', end_date),
            ('state', '=', 'done'),
            ('company_id', '=', company_id.id),
            ('picking_type_id.sequence_code', '=', 'INT'),
            ('picking_type_id.code', '=', 'internal'),
            ('location_id.usage', '=', 'internal'),
            ('location_id.warehouse_id', '=', warehouse_id),
            ('location_dest_id.usage', '=', 'internal'),
            ('location_dest_id.warehouse_id', '=', False),
        ]
        moves = self.env['stock.move.line'].search(domain)
        qty_available = sum(m.qty_done for m in moves)
        if qty_available > 0:
            return qty_available
        else:
            return 0
    
    def _find_internal_return_qty(self, product_id, warehouse_id, start_date, end_date, company_id):
        end_date = end_date+" 23:59:59"
        if start_date:
            date_start = start_date+" 00:00:00"
        else:
            date_start = start_date
        
        domain = [
            ('product_id', '=', product_id),
            ('date', '>=', date_start),
            ('date', '<=', end_date),
            ('state', '=', 'done'),
            ('company_id', '=', company_id.id),
            ('picking_type_id.sequence_code', '=', 'INT'),
            ('picking_type_id.code', '=', 'internal'),
            ('location_id.usage', '=', 'internal'),
            ('location_id.warehouse_id', '=', False),
            ('location_dest_id.usage', '=', 'internal'),
            ('location_dest_id.warehouse_id', '=', warehouse_id),
        ]
        moves = self.env['stock.move.line'].search(domain)
        qty_available = sum(m.qty_done for m in moves)
        if qty_available > 0:
            return qty_available
        else:
            return 0

    def _get_warehouse_wise_product_details(self, data, warehouse):
        product_details = []
        qty_details = []
        if data.get('result_selection') == 'product':
            product_ids = self.env['product.product'].browse(
                data.get('product_ids'))
        else:
            product_ids = self.env['product.product'].search(
                [('categ_id', 'in', data.get('product_categ_ids'))])
        for record in product_ids:
            column_value = {}
            column_value.update({
                'product_code': record.default_code or '',
                'product_name': record.name or '',
                'cost_price': record.standard_price or 0.00,
            })
            for line in data.get('column'):
                outgoing_qty = self._find_outgoing_qty(record.id, warehouse, data.get('column').get(
                    line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
                incoming_qty = self._find_incoming_qty(record.id, warehouse, data.get('column').get(
                    line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
                inventory_qty = self._find_inventory_qty(record.id, warehouse, data.get('column').get(
                    line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
                inventory_get_return_qty = self._find_inventory_return_qty(record.id, warehouse, data.get('column').get(
                    line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
                internal_qty = self._find_internal_qty(record.id, warehouse, data.get('column').get(
                    line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
                internal_get_return_qty = self._find_internal_return_qty(record.id, warehouse, data.get('column').get(
                    line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
                
                total_qty = incoming_qty - outgoing_qty
                if inventory_qty:
                    total_qty += inventory_qty
                if inventory_get_return_qty:
                    total_qty += inventory_get_return_qty
                if internal_qty:
                    total_qty -= internal_qty
                if internal_get_return_qty:
                    total_qty += internal_get_return_qty

                column_value.update({
                    line: total_qty
                })
            qty_details.append(column_value)
        product_details.append(qty_details)
        return product_details

    def _find_outgoing_qty_by_location(self, product_id, location_id, start_date, end_date, company_id):
        end_date = end_date+" 23:59:59"
        if start_date:
            date_start = start_date+" 00:00:00"
        else:
            date_start = start_date
        if not start_date:
            self._cr.execute('''
            SELECT
                SUM(product_uom_qty) AS qty
            FROM stock_move
            WHERE product_id = %s
            AND date<=%s
            AND state='done' 
            AND company_id=%s
            AND location_dest_id in (select id from stock_location where id=%s) 
        ''', (product_id, end_date, company_id.id, location_id))#AND picking_type_id in (select id from stock_picking_type where default_location_src_id=%s and code='outgoing')

        else:
            self._cr.execute('''
	            SELECT
	                SUM(product_uom_qty) AS qty
	            FROM stock_move
	            WHERE product_id = %s
	            AND date>=%s
	            AND date<=%s
	            AND state='done' 
	            AND company_id=%s
	            AND location_dest_id in (select id from stock_location where id=%s) 
	        ''', (product_id, date_start, end_date, company_id.id, location_id))#AND picking_type_id in (select id from stock_picking_type where default_location_src_id=%s and code='outgoing')

        query_res = self._cr.dictfetchall()[0]
        if query_res.get('qty') == None:
            return 0
        else:
            return query_res.get('qty')

    def _find_incoming_qty_by_location(self, product_id, location_id, start_date, end_date, company_id):
        end_date = end_date+" 23:59:59"
        if start_date:
            date_start = start_date+" 00:00:00"
        else:
            date_start = start_date
        if not start_date:
            self._cr.execute('''
            SELECT
                SUM(product_uom_qty) AS qty
            FROM stock_move
            WHERE product_id = %s
            AND date<=%s
            AND state='done' 
            AND company_id=%s
            AND location_id in (select id from stock_location where id=%s) 
        ''', (product_id, end_date, company_id.id, location_id))# AND picking_type_id in (select id from stock_picking_type where default_location_dest_id=%s and code='incoming')
        else:
            self._cr.execute('''
	            SELECT
	                SUM(product_uom_qty) AS qty
	            FROM stock_move
	            WHERE product_id = %s
	            AND date>=%s
	            AND date<=%s
	            AND state='done' 
	            AND company_id=%s
	            AND location_id in (select id from stock_location where id=%s) 
	        ''', (product_id, date_start, end_date, company_id.id, location_id))#AND picking_type_id in (select id from stock_picking_type where default_location_dest_id=%s and code='incoming')

        query_res = self._cr.dictfetchall()[0]
        if query_res.get('qty') == None:
            return 0
        else:
            return query_res.get('qty')

    def _get_location_wise_product_details(self, data, location):
        product_details = []
        qty_details = []
        if data.get('result_selection') == 'product':
            product_ids = self.env['product.product'].browse(
                data.get('product_ids'))
        else:
            product_ids = self.env['product.product'].search(
                [('categ_id', 'in', data.get('product_categ_ids'))])
        for record in product_ids:
            column_value = {}
            column_value.update({
                'product_code': record.default_code or '',
                'product_name': record.name or '',
                'cost_price': record.standard_price or 0.00,
            })
            for line in data.get('column'):
                outgoing_qty = self._find_outgoing_qty_by_location(record.id, location, data.get('column').get(
                    line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
                incoming_qty = self._find_incoming_qty_by_location(record.id, location, data.get('column').get(
                    line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
                column_value.update({
                    line:  outgoing_qty - incoming_qty
                })
            qty_details.append(column_value)
        product_details.append(qty_details)
        return product_details

    def _get_warehouse_name(self, warehouse):
        return self.env['stock.warehouse'].browse(warehouse).name

    def _get_location_name(self, location):
        return self.env['stock.location'].browse(location).complete_name

    @api.model
    def _get_report_values(self, docids, data=None):
        company = self.env['res.company'].browse(data.get('company_id'))
        data['company_id'] = company

        docargs = {
            'doc_model': 'sr.stock.aging.report',
            'data': data,
            'get_warehouse_wise_product_details': self._get_warehouse_wise_product_details,
            'get_warehouse_name': self._get_warehouse_name,
            'get_location_name': self._get_location_name,
            'get_location_wise_product_details': self._get_location_wise_product_details
        }
        return docargs
