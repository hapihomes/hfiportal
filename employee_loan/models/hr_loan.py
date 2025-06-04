from odoo import models, fields

class HrLoan(models.Model):
    _name = "hr.loan"
    _description = "Employee Loan"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    loan_amount = fields.Float(string="Loan Amount", required=True)
    date = fields.Date(string="Date", default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ], string="Status", default="draft")

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_paid(self):
        for rec in self:
            rec.state = 'paid'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'