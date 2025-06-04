from odoo import models, fields

class HrLoan(models.Model):
    _name = 'hr.loan'
    _description = 'Employee Loan'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    amount = fields.Float(string='Loan Amount', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ], string='Status', default='draft')
    date_loan = fields.Date(string='Loan Date', default=fields.Date.context_today)

    def action_approve(self):
        for loan in self:
            loan.state = 'approved'

    def action_paid(self):
        for loan in self:
            loan.state = 'paid'

    def action_set_draft(self):
        for loan in self:
            loan.state = 'draft'
