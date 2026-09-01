from odoo import fields, models


class HrEmployeeLoanPayment(models.Model):
    _name = 'hr.employee.loan.payment'
    _description = 'Employee Loan Payment History'
    _order = 'date desc, id desc'

    loan_id = fields.Many2one('hr.employee.loan', required=True, ondelete='cascade')
    employee_id = fields.Many2one(related='loan_id.employee_id', store=True)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip', ondelete='set null')
    currency_id = fields.Many2one(related='loan_id.currency_id')

    date = fields.Date(required=True, default=fields.Date.context_today)
    amount = fields.Monetary(required=True)
    balance_after = fields.Monetary(string='Balance After Payment')
