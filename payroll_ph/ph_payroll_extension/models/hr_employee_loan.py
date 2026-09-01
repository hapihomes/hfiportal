from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class HrEmployeeLoan(models.Model):
    _name = 'hr.employee.loan'
    _description = 'Employee Loan / Salary Advance'
    _order = 'date_granted desc, id desc'

    name = fields.Char(string='Reference', copy=False, default='New')
    employee_id = fields.Many2one('hr.employee', required=True, tracking=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    currency_id = fields.Many2one(related='company_id.currency_id')

    loan_type_id = fields.Many2one('ph.loan.type', required=True, tracking=True)
    is_government = fields.Boolean(related='loan_type_id.is_government', store=True)

    date_granted = fields.Date(default=fields.Date.context_today, required=True)
    principal_amount = fields.Monetary(required=True)
    monthly_amortization = fields.Monetary(required=True)
    number_of_installments = fields.Integer(
        compute='_compute_number_of_installments', store=True,
        help='Estimated number of installments based on the principal amount and monthly amortization.')

    balance = fields.Monetary(
        string='Outstanding Balance', copy=False,
        help='Remaining amount still to be deducted from payslips.')
    total_paid = fields.Monetary(compute='_compute_total_paid', store=True)
    payment_count = fields.Integer(
        string='Deductions Made', compute='_compute_payment_count', store=True,
        help='Number of payslip deductions posted against this loan so far.')
    remaining_installments = fields.Integer(
        string='Deductions Remaining', compute='_compute_remaining_installments', store=True,
        help='Estimated number of remaining monthly deductions based on the current outstanding balance.')
    estimated_end_date = fields.Date(
        string='Estimated Payoff Date', compute='_compute_estimated_end_date', store=True,
        help='Projected date the loan will be fully paid off, based on the current balance, monthly '
             'amortization and payment history. Actual date may vary if a payslip period is skipped.')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Fully Paid'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True, copy=False)

    payment_ids = fields.One2many('hr.employee.loan.payment', 'loan_id', string='Payment History')
    notes = fields.Text()

    @api.depends('principal_amount', 'monthly_amortization')
    def _compute_number_of_installments(self):
        for loan in self:
            if loan.monthly_amortization:
                loan.number_of_installments = int(
                    -(-loan.principal_amount // loan.monthly_amortization))  # ceil division
            else:
                loan.number_of_installments = 0

    @api.depends('payment_ids.amount')
    def _compute_total_paid(self):
        for loan in self:
            loan.total_paid = sum(loan.payment_ids.mapped('amount'))

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for loan in self:
            loan.payment_count = len(loan.payment_ids)

    @api.depends('balance', 'monthly_amortization')
    def _compute_remaining_installments(self):
        for loan in self:
            if loan.monthly_amortization and loan.balance > 0:
                loan.remaining_installments = int(-(-loan.balance // loan.monthly_amortization))  # ceil division
            else:
                loan.remaining_installments = 0

    @api.depends('payment_ids.date', 'date_granted', 'remaining_installments', 'state')
    def _compute_estimated_end_date(self):
        for loan in self:
            last_payment_date = max(loan.payment_ids.mapped('date'), default=None)
            base_date = last_payment_date or loan.date_granted
            if loan.state == 'done':
                loan.estimated_end_date = base_date
            elif base_date and loan.remaining_installments:
                loan.estimated_end_date = base_date + relativedelta(months=loan.remaining_installments)
            else:
                loan.estimated_end_date = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.employee.loan') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        for loan in self:
            if loan.state != 'draft':
                raise UserError(self.env._('Only draft loans can be confirmed.'))
            if loan.principal_amount <= 0 or loan.monthly_amortization <= 0:
                raise UserError(self.env._('The principal amount and monthly amortization must be greater than zero.'))
            loan.balance = loan.principal_amount
        self.write({'state': 'running'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft', 'balance': 0.0})
