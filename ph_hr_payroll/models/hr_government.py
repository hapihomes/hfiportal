from odoo import models, fields

# Government contribution model for SSS, PhilHealth, Pag-IBIG
class HrGovernmentContribution(models.Model):
    _name = 'hr.government.contribution'
    _description = 'Government Contributions'

    name = fields.Selection([
        ('sss', 'SSS'),
        ('philhealth', 'PhilHealth'),
        ('pagibig', 'Pag-IBIG')
    ], required=True)  # Type of contribution
    employee_id = fields.Many2one('hr.employee')  # Employee receiving deduction
    amount = fields.Float()  # Deduction amount
