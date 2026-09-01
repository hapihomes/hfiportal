from odoo import fields, models


class PhAllowanceType(models.Model):
    _name = 'ph.allowance.type'
    _description = 'PH Allowance Type'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    code = fields.Char(required=True, help='Technical code, for internal reference/reporting.')
    sequence = fields.Integer(default=10)
    is_taxable = fields.Boolean(
        string='Taxable',
        help='If checked, this allowance is included in taxable income. '
             'Otherwise it is treated as a non-taxable (de minimis) benefit.')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The allowance type code must be unique.'),
    ]
