from odoo import models, fields

# Loan model to manage employee loans
class HrLoan(models.Model):
    _name = 'hr.loan'
    _description = 'Employee Loan'

    employee_id = fields.Many2one('hr.employee', required=True)  # Reference to the employee
    amount = fields.Float('Loan Amount', required=True)  # Total loan amount
    monthly_deduction = fields.Float('Monthly Deduction')  # Monthly deduction amount
    remaining_amount = fields.Float('Remaining Amount')  # Remaining loan balance
    state = fields.Selection([('active', 'Active'), ('done', 'Done')], default='active')  # Status of the loan
