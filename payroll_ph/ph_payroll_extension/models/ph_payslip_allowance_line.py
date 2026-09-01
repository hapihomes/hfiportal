from odoo import api, fields, models


class PhPayslipAllowanceLine(models.Model):
    _name = 'ph.payslip.allowance.line'
    _description = 'Payslip Allowance Line'
    _order = 'sequence, id'

    payslip_id = fields.Many2one('hr.payslip', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='payslip_id.company_id', store=True)
    currency_id = fields.Many2one(related='payslip_id.company_id.currency_id')
    sequence = fields.Integer(default=10)

    allowance_type_id = fields.Many2one('ph.allowance.type', required=True)
    name = fields.Char(string='Description')
    is_taxable = fields.Boolean(related='allowance_type_id.is_taxable', store=True, readonly=True)
    amount = fields.Monetary(required=True)

    @api.onchange('allowance_type_id')
    def _onchange_allowance_type_id(self):
        for line in self:
            if line.allowance_type_id and not line.name:
                line.name = line.allowance_type_id.name
