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


class StockAgingReport(models.AbstractModel):
	_name = 'report.sr_stock_aging_report.report_stock_aging' 

	def _find_outgoing_qty(self, product_id, warehouse_id, start_date, end_date, company_id):
		if not start_date:
			self._cr.execute('''
            SELECT
                SUM(product_uom_qty) AS qty
            FROM stock_move
            WHERE product_id = %s
            AND date<=%s
            AND state='done' 
            AND company_id=%s
            AND picking_type_id in (select id from stock_picking_type where warehouse_id=%s and code='outgoing')
            AND location_dest_id in (select id from stock_location where usage='customer') 
        ''', (product_id, end_date, company_id.id, warehouse_id))
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
	            AND picking_type_id in (select id from stock_picking_type where warehouse_id=%s and code='outgoing')
	            AND location_dest_id in (select id from stock_location where usage='customer') 
	        ''', (product_id, start_date, end_date, company_id.id, warehouse_id))

		query_res = self._cr.dictfetchall()[0]
		if query_res.get('qty') == None:
			return 0
		else:
			return query_res.get('qty')

	def _find_incoming_qty(self, product_id, warehouse_id, start_date, end_date, company_id):
		if not start_date:
			self._cr.execute('''
            SELECT
                SUM(product_uom_qty) AS qty
            FROM stock_move
            WHERE product_id = %s
            AND date<=%s
            AND state='done' 
            AND company_id=%s
            AND picking_type_id in (select id from stock_picking_type where warehouse_id=%s and code='incoming')
            AND location_dest_id in (select id from stock_location where usage='internal') 
        ''', (product_id, end_date, company_id.id, warehouse_id))
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
	            AND picking_type_id in (select id from stock_picking_type where warehouse_id=%s and code='incoming')
	            AND location_dest_id in (select id from stock_location where usage='internal') 
	        ''', (product_id, start_date, end_date, company_id.id, warehouse_id))

		query_res = self._cr.dictfetchall()[0]
		if query_res.get('qty') == None:
			return 0
		else:
			return query_res.get('qty')

	def _get_warehouse_wise_product_details(self, data, warehouse):
		product_details = []
		qty_details = []
		if data.get('result_selection') == 'product':
			product_ids = self.env['product.product'].browse(data.get('product_ids'))
		else:
			product_ids = self.env['product.product'].search([('categ_id', 'in', data.get('product_categ_ids'))])
		for record in product_ids:
			column_value = {}
			column_value.update({
					'product_code' : record.default_code or '',
					'product_name': record.name or '',
					'cost_price' : record.standard_price  or 0.00,
				})
			for line in data.get('column'):
				outgoing_qty = self._find_outgoing_qty(record.id, warehouse, data.get('column').get(line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
				incoming_qty = self._find_incoming_qty(record.id, warehouse, data.get('column').get(line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
				column_value.update({
					line: incoming_qty - outgoing_qty
					})
			qty_details.append(column_value)
		product_details.append(qty_details)
		return product_details

	def _find_outgoing_qty_by_location(self, product_id, location_id, start_date, end_date, company_id):
		if not start_date:
			self._cr.execute('''
            SELECT
                SUM(product_uom_qty) AS qty
            FROM stock_move
            WHERE product_id = %s
            AND date<=%s
            AND state='done' 
            AND company_id=%s
            AND picking_type_id in (select id from stock_picking_type where default_location_src_id=%s and code='outgoing')
            AND location_dest_id in (select id from stock_location where usage='customer') 
        ''', (product_id, end_date, company_id.id, location_id))
			
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
	            AND picking_type_id in (select id from stock_picking_type where default_location_src_id=%s and code='outgoing')
	            AND location_dest_id in (select id from stock_location where usage='customer') 
	        ''', (product_id, start_date, end_date, company_id.id, location_id))

		query_res = self._cr.dictfetchall()[0]
		if query_res.get('qty') == None:
			return 0
		else:
			return query_res.get('qty')

	def _find_incoming_qty_by_location(self, product_id, location_id, start_date, end_date, company_id):
		if not start_date:
			self._cr.execute('''
            SELECT
                SUM(product_uom_qty) AS qty
            FROM stock_move
            WHERE product_id = %s
            AND date<=%s
            AND state='done' 
            AND company_id=%s
            AND picking_type_id in (select id from stock_picking_type where default_location_dest_id=%s and code='incoming')
            AND location_dest_id in (select id from stock_location where usage='internal') 
        ''', (product_id, end_date, company_id.id, location_id))
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
	            AND picking_type_id in (select id from stock_picking_type where default_location_dest_id=%s and code='incoming')
	            AND location_dest_id in (select id from stock_location where usage='internal') 
	        ''', (product_id, start_date, end_date, company_id.id, location_id))

		query_res = self._cr.dictfetchall()[0]
		if query_res.get('qty') == None:
			return 0
		else:
			return query_res.get('qty')

	def _get_location_wise_product_details(self, data, location):
		product_details = []
		qty_details = []
		if data.get('result_selection') == 'product':
			product_ids = self.env['product.product'].browse(data.get('product_ids'))
		else:
			product_ids = self.env['product.product'].search([('categ_id', 'in', data.get('product_categ_ids'))])
		for record in product_ids:
			column_value = {}
			column_value.update({
					'product_code' : record.default_code or '',
					'product_name': record.name or '',
					'cost_price' : record.standard_price  or 0.00,
				})
			for line in data.get('column'):
				outgoing_qty = self._find_outgoing_qty_by_location(record.id, location, data.get('column').get(line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
				incoming_qty = self._find_incoming_qty_by_location(record.id, location, data.get('column').get(line).get('start'), data.get('column').get(line).get('stop'), data.get('company_id'))
				column_value.update({
					line: incoming_qty - outgoing_qty
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
				   'get_warehouse_wise_product_details':self._get_warehouse_wise_product_details,
 				   'get_warehouse_name':self._get_warehouse_name,
 				   'get_location_name':self._get_location_name,
 				   'get_location_wise_product_details':self._get_location_wise_product_details
				   }
		return docargs
