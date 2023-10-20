# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import tempfile
from odoo.tools.misc import xlwt
import io
import base64
import time
from dateutil.relativedelta import relativedelta
from pytz import timezone


class Inventory_Age_Breakdown_analysis_wizard(models.Model):
    _name = 'inventory.age.breakdown.report.wiz'
    _description = 'Inventory Age Breakdown Analysis Report'


    company_ids = fields.Many2many("res.company", string="Company")
    category_ids = fields.Many2many("product.category", string="Product Category")
    product_ids = fields.Many2many("product.product", string="Product")
    days_breakdown = fields.Integer("Days for Breakdown", default=30)
    

    def print_inventory_age_breakdown_report(self):

        filename = 'Stock Age Breakdown Report' + '.xls'
        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Stock Age Breakdown Report')
        font = xlwt.Font()
        font.bold = True
        for_left = xlwt.easyxf(
            "font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
        for_left_not_bold = xlwt.easyxf("font: color black; align: horiz left",num_format_str='0.00')
        for_center_bold = xlwt.easyxf(
            "font: bold 1, color black; align: horiz center")
        GREEN_TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 250;'
            'align: vertical center, horizontal center, wrap on;'
            'borders: top double, bottom double, left double, right double;'
        )
        style = xlwt.easyxf(
            'font:height 400, bold True, name Arial; align: horiz center, vert center;borders: top medium,right medium,bottom medium,left medium')
    
        alignment = xlwt.Alignment()  # Create Alignment
        alignment.horz = xlwt.Alignment.HORZ_RIGHT
        style = xlwt.easyxf('align: wrap yes')
        style.num_format_str = '0.00'

        worksheet.row(0).height = 500
        worksheet.col(0).width = 10000
        worksheet.col(1).width = 7000
        worksheet.col(2).width = 4000
        worksheet.col(3).width = 4000
        worksheet.col(4).width = 4000
        worksheet.col(5).width = 4000
        worksheet.col(6).width = 4000
        worksheet.col(7).width = 4000


       
        worksheet.write_merge(0, 0, 0, 5, 'Stock Age Breakdown Report', GREEN_TABLE_HEADER)

        row= 1
        col=0
        worksheet.write(row, col, 'Company' or '', for_left)
        col=1
        for i in self.company_ids:
            company=[]
            company.append(i.name)
            worksheet.write(row, col, company or '', for_left_not_bold)
            col+=1

        row = 2
        sums=1
        
        one=(self.days_breakdown)*1
        two=(self.days_breakdown)*2
        three=(self.days_breakdown)*3
        four=(self.days_breakdown)*4
        five=(self.days_breakdown)*5
        six=(self.days_breakdown)*6

        one_1=one +sums
        two_1=two +sums
        three_1=three +sums
        four_1=four +sums
        five_1=five +sums
        six_1=six +sums
        
        

        worksheet.write(row, 0, '' or '', for_left)
        worksheet.write(row, 1, '' or '', for_left)
        worksheet.write(row, 2, '' or '', for_left)
        worksheet.write(row, 3, '' or '', for_left)
        worksheet.write(row, 4, '' or '', for_left)
        worksheet.write_merge(row,row, 5,6, str(sums) + ' To '+ str(one) or '', for_left)
        worksheet.write_merge(row,row, 7,8, str(one_1) + ' To '+ str(two) or '', for_left)
        worksheet.write_merge(row,row, 9,10, str(two_1) + ' To '+ str(three) or '', for_left)
        worksheet.write_merge(row,row, 11,12, str(three_1) + ' To '+ str(four) or '', for_left)
        worksheet.write_merge(row,row, 13,14, str(four_1) + ' To '+ str(five) or '', for_left)
        worksheet.write_merge(row,row, 15,16, str(five_1) + ' To '+ str(six) or '', for_left)
        worksheet.write_merge(row,row, 17,18, ' Oldest Then '+ str(six_1) or '', for_left)

        row = 4

        worksheet.write(row, 0, 'Product Name' or '', for_left)
        worksheet.write(row, 1,'Company Name' or '', for_left )
        worksheet.write(row, 2, 'Category' or '', for_left)
        worksheet.write(row, 3, 'Total Stock' or '', for_left)
        worksheet.write(row, 4, 'Stock Value' or '', for_left)
        worksheet.write(row, 5, 'Stock' or '', for_left)
        worksheet.write(row, 6, 'Value' or '', for_left)
        worksheet.write(row, 7, 'Stock' or '', for_left)
        worksheet.write(row, 8, 'Value' or '', for_left)
        worksheet.write(row, 9, 'Stock' or '', for_left)
        worksheet.write(row, 10, 'Value' or '', for_left)
        worksheet.write(row, 11, 'Stock' or '', for_left)
        worksheet.write(row, 12, 'Value' or '', for_left)
        worksheet.write(row, 13, 'Stock' or '', for_left)
        worksheet.write(row, 14, 'Value' or '', for_left)
        worksheet.write(row, 15, 'Stock' or '', for_left)
        worksheet.write(row, 16, 'Value' or '', for_left)
        worksheet.write(row, 17, 'Stock' or '', for_left)
        worksheet.write(row, 18, 'Value' or '', for_left)

        product_ids = self.env['product.product']

        if self.category_ids and self.product_ids : 
            product_ids += self.env['product.product'].search(['|',('id','in',self.product_ids.ids),('categ_id','in',self.category_ids.ids)])

        elif self.category_ids:
            product_ids = self.env['product.product'].search([('categ_id','in',self.category_ids.ids)])

        elif self.product_ids:
            product_ids += self.product_ids

        elif not product_ids:
            product_ids = self.env['product.product'].search([])

        rows = 5
        sr_no = 0
        a = datetime.now() - timedelta(days=one)
        b = datetime.now() - timedelta(days=two)
        c = datetime.now() - timedelta(days=three)
        d = datetime.now() - timedelta(days=four)
        e = datetime.now() - timedelta(days=five)
        f = datetime.now() - timedelta(days=six)
        g = datetime.now() - timedelta(days=six+100)

        stock_value = 0
        available_quantity = 0.0
        if self.company_ids:
            product_ids = product_ids.filtered(lambda x : x.company_id in self.company_ids or not x.company_id)
        
        for company in self.company_ids: 
            for product_id in product_ids:
                qty_to_carry = 0.0

                domain = [('product_id','=',product_id.id)]
                
                if self.company_ids:
                    domain += [('company_id','in',self.company_ids.ids)]
                
                    location_id = self.env['stock.location'].sudo().search([('usage', 'in', ['internal']),('company_id','=',company.id)])
                    location_dest_id = self.env['stock.location'].sudo().search([('usage', 'in', ['internal','transit','inventory']),('company_id','=',company.id)])
                else:
                    location_id = self.env['stock.location'].sudo().search([('usage', 'in', ['internal'])])
                    location_dest_id = self.env['stock.location'].sudo().search([('usage', 'in', ['internal','transit','inventory'])])
                    
                domain += [('location_id', 'in', location_id.ids)]
                domain += [('state','=','done')]
                domain +=[('picking_id.picking_type_id.code', '=', 'incoming')]
                
                move_lines = self.env['stock.move.line'].sudo().search(domain)
                qty_sold = sum(line.qty_done for line in move_lines)

                qty_to_carry = qty_sold

                col = 0
                worksheet.write(rows, col, product_id.display_name or '', for_left_not_bold)
                col += 1
                worksheet.write(rows, col, company.name or '', for_left_not_bold)
                col += 1
                worksheet.write(rows, col, product_id.categ_id.name_get()[0][1] or '', for_left_not_bold)
                col += 1
                
                stock_qty_obj = self.env['stock.quant']                        
                stock_qty_lines = stock_qty_obj.sudo().search([('product_id', '=', product_id.id),('company_id','=',company.id)])
                available_quantity = sum(row.quantity for row in stock_qty_lines if row.quantity > 0 and row.location_id.location_id)
                worksheet.write(rows, col, available_quantity  or '0', for_left_not_bold)
                
                col += 1
                stock_value = available_quantity * product_id.with_company(company).standard_price
                worksheet.write(rows, col, stock_value or '0', for_left_not_bold)
                col += 1

                col += 14
                for i in range(7, 0, -1):
                    start = datetime.now() if i == 1 else (datetime.now() - relativedelta(days=self.days_breakdown*(i-1)))
                    stop = start - relativedelta(days=self.days_breakdown)

                    domain = [('date','<=',str(start)),('date','>',str(stop))]
                    domain += [('product_id','=',product_id.id)]
                    domain += [('state','=','done')]
                    if self.company_ids:
                        domain += [('company_id','=',company.id)]
                    domain += [('location_usage', 'not in', ['internal','transit']),('location_dest_usage' ,'in', ['internal','transit',])]
                    move_lines = self.env['stock.move.line'].sudo().search(domain)

                    new_domain = [('date','<=',str(start)),('date','>',str(stop))]
                    new_domain += [('product_id','=',product_id.id)]
                    new_domain += [('state','=','done')]
                    if self.company_ids:
                        new_domain += [('company_id','=',company.id)]
                    new_domain += [('location_usage', 'in', ['internal','transit']),('location_dest_usage' ,'not in', ['internal','transit'])]
                    new_move_lines = self.env['stock.move.line'].sudo().search(new_domain)
                    
                    extra_domain = [('date','<=',str(start)),('date','>',str(stop))]
                    extra_domain += [('product_id','=',product_id.id)]
                    extra_domain += [('state','=','done')]
                    if self.company_ids:
                        extra_domain += [('company_id','=',company.id)]
                    extra_domain += [('picking_type_id.code', '=', 'internal'),('location_id.usage', 'in', ['internal']),('location_dest_id.usage', 'in', ['internal'])]
                    extra_move_lines = self.env['stock.move.line'].sudo().search(extra_domain)
                    
                    extra_qty_on_hand = sum(line.qty_done for line in extra_move_lines if not line.location_dest_id.location_id)
                    new_qty_on_hand = sum(line.qty_done for line in new_move_lines)
                    qty_on_hand = sum(line.qty_done for line in move_lines if line.location_dest_id.location_id)

                    final_qty = qty_on_hand - new_qty_on_hand + extra_qty_on_hand
                    
                    if qty_on_hand > 0.0:
                        qty_to_carry = qty_to_carry - qty_on_hand

                        if qty_to_carry > 0.0:
                            qty_on_hand = 0.0
                        if qty_to_carry == 0.0:
                            qty_to_carry == 0.0
                        else:
                            qty_on_hand = qty_to_carry
                            qty_to_carry = 0.0

                    col -= 1
                    worksheet.write(rows, col, abs(final_qty) *  product_id.with_company(company).standard_price or '0.0', for_left_not_bold)
                    col -= 1
                    worksheet.write(rows, col, abs(final_qty) or '0.0', for_left_not_bold)


                rows += 1

        fp = io.BytesIO()
        workbook.save(fp)
        age_breakdown_id = self.env['inventory.age.breakdown.extended'].create({
            'excel_file': base64.b64encode(fp.getvalue()),
            'file_name': filename
        })
        fp.close()

        return{
            'view_mode': 'form',
            'res_id':age_breakdown_id.id,
            'res_model': 'inventory.age.breakdown.extended',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new',
        }


class Inventory_Age_Breakdown_analysis_Extended(models.TransientModel):
    _name = 'inventory.age.breakdown.extended'
    _description = "Stock Age Breakdown Excel Extended"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)

   