from odoo import fields, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    ph_pay_frequency = fields.Selection(
        [
            ('monthly', 'Monthly (one payslip per month)'),
            ('semi_monthly', 'Semi-monthly (two payslips per month)'),
        ],
        string='PH Pay Frequency', default='semi_monthly', required=True,
        help='Controls how Basic Salary is prorated: monthly pays the full '
             'contract wage each payslip, semi-monthly pays half.')

    ph_deduction_cutoff = fields.Selection(
        [
            ('first', 'First cutoff of the month'),
            ('second', 'Second cutoff of the month'),
            ('both', 'Split evenly across both cutoffs'),
        ],
        string='Government/Loan Deductions Applied On', default='second', required=True,
        help='For a semi-monthly schedule, which payslip(s) carry the full '
             'monthly SSS/PhilHealth/HDMF contributions and loan '
             'amortizations. Ignored for a monthly schedule (always applied).')

    ph_cutoff_split_day = fields.Integer(
        string='Cutoff Split Day', default=15, required=True,
        help='Day of the month used to tell the two semi-monthly cutoffs '
             'apart: a payslip whose period-end date falls on or before this '
             'day is the "first" cutoff, after it the "second" cutoff. '
             'E.g. with cutoffs ending the 10th and 26th, leave this at 15.')

    ph_pay_treatment = fields.Selection(
        [
            ('monthly_paid', 'Monthly-paid'),
            ('daily_paid', 'Daily-paid'),
        ],
        string='PH Pay Treatment', default='monthly_paid', required=True,
        help='Monthly-paid: Basic Salary is the contract wage (prorated per '
             'the Pay Frequency above), unaffected by attendance. '
             'Daily-paid: the contract wage is treated as a DAILY rate, and '
             'Basic Salary = daily rate x actual days worked this period '
             '(from attendance/worked days), excluding days paid separately '
             'as Overtime.')

    ph_standard_monthly_hours = fields.Float(
        string='Standard Monthly Working Hours', default=208.0, required=True,
        help='Contract wage divided by this number gives the hourly rate '
             'used for Overtime pay. Common PH convention: 8 hours/day x '
             '26 days/month = 208.')
