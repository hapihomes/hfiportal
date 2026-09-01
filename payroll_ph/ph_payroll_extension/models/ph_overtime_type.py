from odoo import fields, models


class PhOvertimeType(models.Model):
    _name = 'ph.overtime.type'
    _description = 'PH Overtime Type'
    _order = 'sequence, id'

    name = fields.Char(required=True, help='e.g. Ordinary Day Overtime, Rest Day Overtime, Regular Holiday Overtime.')
    work_entry_code = fields.Char(
        string='Work Entry Type Code', required=True,
        help='The exact Code of the Work Entry Type (Employees > Configuration > Work Entry '
             'Types) that represents this kind of overtime in attendance/worked days. Hours '
             'logged under this code on the payslip are paid at the rate below.')
    multiplier = fields.Float(
        string='Rate (%)', required=True, default=125.0,
        help='Percentage of the hourly rate paid for this type of overtime, e.g. 125 for 125%.')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('work_entry_code_uniq', 'unique(work_entry_code)',
         'A PH Overtime Type already exists for this Work Entry Type code.'),
    ]
