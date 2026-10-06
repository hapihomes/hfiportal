from odoo import api, models


class ReportStockAgeing(models.AbstractModel):
    # Odoo looks for a model named "report.<report_name>" to feed the QWeb
    # template of a PDF report; <report_name> is defined in
    # views/stock_ageing_report_templates.xml.
    _name = 'report.stock_ageing_report.report_stock_ageing'
    _description = 'Ageing Products PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepare the variables available inside the QWeb template."""
        docs = self.env['stock.ageing.report'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.ageing.report',
            'lines': docs._export_lines(),   # one line per location/product
            'company': self.env.company,
        }
