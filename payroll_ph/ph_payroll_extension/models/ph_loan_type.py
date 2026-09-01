from odoo import fields, models


class PhLoanType(models.Model):
    _name = 'ph.loan.type'
    _description = 'PH Loan Type'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    code = fields.Char(
        required=True,
        help='Technical code. Must match the code of the related payslip '
             'Other Input Type so the deduction can be picked up by the '
             'matching salary rule (e.g. SSSLOAN, HDMFLOAN, COMPANYLOAN, SALARYADV).')
    sequence = fields.Integer(default=10)
    is_government = fields.Boolean(
        string='Government Loan',
        help='Government-mandated loan (SSS, HDMF/Pag-IBIG) as opposed to an internal company loan.')
    input_type_id = fields.Many2one(
        'hr.payslip.input.type', string='Payslip Input Type', required=True,
        help='The Other Input Type used to carry the computed deduction into the payslip salary rules.')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The loan type code must be unique.'),
    ]
