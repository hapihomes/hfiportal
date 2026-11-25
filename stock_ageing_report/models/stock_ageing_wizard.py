"""
Options window (wizard) opened from Inventory > Reporting > Ageing Products.

The user picks an output (pivot / Excel / CSV / PDF), optionally limits the
warehouses, and decides whether to recompute the snapshot first.
"""
import base64
import csv
import io

from odoo import fields, models
from odoo.exceptions import UserError

# Column titles used by the CSV and Excel exports. The order MUST match
# the order of the values returned by `_row()` below.
HEADERS = ['Warehouse', 'Location', 'Internal Reference', 'Product', 'Never Sold',
           '0 - 30 Days', '30 - 90 Days', '90 - 180 Days', '180 - 365 Days',
           '365+ Days', 'Total Quantity', 'Available Quantity', 'Total Cost',
           '0 - 30 Cost', '30 - 90 Cost', '90 - 180 Cost', '180 - 365 Cost', '365+ Cost']


class StockAgeingWizard(models.TransientModel):
    # TransientModel = temporary records, cleaned automatically by Odoo.
    _name = 'stock.ageing.wizard'
    _description = 'Ageing Products Options'

    output_type = fields.Selection([
        ('pivot', 'Pivot (on screen)'),
        ('xlsx', 'Excel (.xlsx)'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
    ], string='Output', default='pivot', required=True)
    recompute = fields.Boolean(
        string='Recompute from full stock history', default=True,
        help='Replays every stock movement since the start of the database. '
             'Untick to reuse the last snapshot (faster; a nightly job also refreshes it).')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses',
                                     help='Leave empty for all warehouses.')
    # Informational: when the saved snapshot was last written.
    last_refresh = fields.Datetime(compute='_compute_last_refresh')

    def _compute_last_refresh(self):
        # The newest write_date among the snapshot rows = last rebuild time.
        last = self.env['stock.ageing.report'].search([], order='write_date desc', limit=1)
        for wiz in self:
            wiz.last_refresh = last.write_date

    # ------------------------------------------------------------------
    # "Generate" button
    # ------------------------------------------------------------------
    def action_generate(self):
        self.ensure_one()
        Report = self.env['stock.ageing.report']

        # 1) Rebuild the snapshot if asked (or if there is none yet).
        if self.recompute or not Report.search_count([], limit=1):
            Report._refresh()

        # 2) Optional warehouse filter.
        domain = []
        if self.warehouse_ids:
            domain = [('warehouse_id', 'in', self.warehouse_ids.ids)]

        # 3a) Pivot: open the normal window action with our domain applied.
        if self.output_type == 'pivot':
            action = self.env['ir.actions.act_window']._for_xml_id(
                'stock_ageing_report.action_stock_ageing_report')
            action['domain'] = domain
            return action

        # 3b) Any export: read the snapshot rows first.
        records = Report.search(domain)
        if not records:
            raise UserError('There is no stock to report for the selected options.')

        # PDF is rendered by the QWeb report (see stock_ageing_report_pdf.py).
        if self.output_type == 'pdf':
            return self.env.ref('stock_ageing_report.action_report_stock_ageing').report_action(records)

        # CSV / Excel: build the file in memory, one row per location+product.
        lines = records._export_lines()
        rows = [self._row(line) for line in lines]
        total_rows = [self._row(line) for line in records._product_totals(lines)]
        if self.output_type == 'csv':
            data, name, mime = self._build_csv(rows, total_rows), 'ageing_products.csv', 'text/csv'
        else:
            data, name = self._build_xlsx(rows, total_rows), 'ageing_products.xlsx'
            mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        # Save the file as an attachment and send the browser to download it.
        attachment = self.env['ir.attachment'].create({
            'name': name, 'datas': base64.b64encode(data), 'mimetype': mime,
            'res_model': self._name, 'res_id': self.id,
        })
        return {'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id, 'target': 'self'}

    # ------------------------------------------------------------------
    # File builders
    # ------------------------------------------------------------------
    @staticmethod
    def _row(line):
        """Turn one export line (dict) into a list matching HEADERS."""
        return [line['warehouse'], line['location'], line['code'], line['product'],
                'Yes' if line['never_sold'] else 'No',
                line['qty_0_30'], line['qty_30_90'], line['qty_90_180'],
                line['qty_180_365'], line['qty_365_plus'], line['quantity'], line['available_quantity'], line['value'],
                line['cost_0_30'], line['cost_30_90'], line['cost_90_180'],
                line['cost_180_365'], line['cost_365_plus']]

    @staticmethod
    def _build_csv(rows, total_rows):
        """Return the CSV file content as bytes."""
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(HEADERS)
        writer.writerows(rows)
        # Second section: total of each product across all locations.
        writer.writerow([])
        writer.writerow(['Totals per Product (all locations)'])
        writer.writerow(HEADERS)
        writer.writerows(total_rows)
        # utf-8-sig adds a BOM so Excel opens accents/special characters correctly.
        return out.getvalue().encode('utf-8-sig')

    @staticmethod
    def _build_xlsx(rows, total_rows):
        """Return the .xlsx file content as bytes (uses xlsxwriter, bundled with Odoo)."""
        import xlsxwriter
        out = io.BytesIO()
        book = xlsxwriter.Workbook(out, {'in_memory': True})
        head = book.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        num = book.add_format({'num_format': '#,##0.00'})

        # Sheet 1: one row per location + product. Sheet 2: one row per
        # product, summed across all locations.
        for title, sheet_rows in (('Ageing Products', rows),
                                  ('Totals per Product', total_rows)):
            sheet = book.add_worksheet(title)
            # Header row.
            for col, header in enumerate(HEADERS):
                sheet.write(0, col, header, head)
            # Data rows: columns 5+ are numbers, so they get the number format.
            for r, row in enumerate(sheet_rows, start=1):
                for c, val in enumerate(row):
                    sheet.write(r, c, val, num if c >= 5 else None)
            # Column widths and frozen header row.
            sheet.set_column(0, 1, 28)
            sheet.set_column(2, 2, 16)
            sheet.set_column(3, 3, 40)
            sheet.set_column(4, 17, 14)
            sheet.freeze_panes(1, 0)
        book.close()
        return out.getvalue()
