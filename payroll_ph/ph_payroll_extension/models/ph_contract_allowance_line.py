from odoo import fields, models


class PhContractAllowanceLine(models.Model):
    _name = 'ph.contract.allowance.line'
    _description = 'Recurring Contract Allowance'
    _order = 'sequence, id'

    contract_id = fields.Many2one('hr.version', string='Contract', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='contract_id.company_id', store=True)
    currency_id = fields.Many2one(related='contract_id.company_id.currency_id')
    sequence = fields.Integer(default=10)

    allowance_type_id = fields.Many2one('ph.allowance.type', required=True)
    is_taxable = fields.Boolean(related='allowance_type_id.is_taxable', store=True, readonly=True)
    amount = fields.Monetary(
        required=True,
        help='Default recurring amount that will be copied onto every new payslip generated for this contract.')
