import logging

from odoo import Command, api, fields, models

from .ph_config import configure_ph_extension

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _ph_get_contract(self):
        """Return the Contract/Version record linked to this payslip,
        without hard-coding a field name: this build calls the model
        'hr.version' and even the salary-rule engine's own local variable
        for it is 'version' rather than 'contract', so we look up the
        actual field on hr.payslip by its target model instead of guessing.
        """
        self.ensure_one()
        for field_name, field in self._fields.items():
            if getattr(field, 'type', None) == 'many2one' and \
                    getattr(field, 'comodel_name', None) in ('hr.version', 'hr.contract'):
                return self[field_name]
        return self.env['hr.version']

    def _register_hook(self):
        # Re-attach any PH UI extensions (menu, payslip/structure/contract
        # tabs, report addendum) that couldn't be attached yet -- runs on
        # every module upgrade and server restart, not just a fresh install,
        # so newly added attachments self-heal without requiring a clean
        # reinstall.
        super()._register_hook()
        configure_ph_extension(self.env)

    commission_amount = fields.Monetary(
        string='Commission', default=0.0, tracking=True,
        help='Manually entered sales commission for this pay period. '
             'Feeds into taxable income and gross pay through the COMMISSION salary rule.')

    allowance_line_ids = fields.One2many(
        'ph.payslip.allowance.line', 'payslip_id', string='Allowances')
    total_taxable_allowance = fields.Monetary(
        string='Total Taxable Allowances', compute='_compute_allowance_totals', store=True)
    total_nontaxable_allowance = fields.Monetary(
        string='Total Non-Taxable Allowances', compute='_compute_allowance_totals', store=True)

    ph_loans_posted = fields.Boolean(
        string='PH Loan Deductions Posted', copy=False, default=False,
        help='Technical flag preventing loan balances from being deducted more than once for the same payslip.')

    overtime_hours = fields.Float(
        string='Overtime Hours', copy=False,
        help='Total overtime hours this period, read from attendance/worked days per the '
             'PH Overtime Types configured under PH Payroll Settings. Refreshed on Compute Sheet '
             '(plain stored field, not a live compute, since this build\'s worked-days field name '
             'cannot be safely assumed for an @api.depends declaration -- see _ph_get_worked_days_lines).')

    @api.depends('allowance_line_ids.amount', 'allowance_line_ids.is_taxable')
    def _compute_allowance_totals(self):
        for slip in self:
            taxable = 0.0
            nontaxable = 0.0
            for line in slip.allowance_line_ids:
                if line.is_taxable:
                    taxable += line.amount
                else:
                    nontaxable += line.amount
            slip.total_taxable_allowance = taxable
            slip.total_nontaxable_allowance = nontaxable

    @api.model_create_multi
    def create(self, vals_list):
        slips = super().create(vals_list)
        for slip in slips:
            contract = slip._ph_get_contract()
            if contract and not slip.allowance_line_ids:
                defaults = contract.ph_recurring_allowance_ids
                if defaults:
                    slip.allowance_line_ids = [
                        Command.create({
                            'allowance_type_id': line.allowance_type_id.id,
                            'name': line.allowance_type_id.name,
                            'amount': line.amount,
                        }) for line in defaults
                    ]
        return slips

    def _ph_get_pay_policy(self):
        """Return (frequency, deduction_cutoff, split_day) read from this
        payslip's Salary Structure, with safe fallbacks if the structure
        doesn't carry the PH config fields (e.g. a non-PH structure) or
        isn't set yet.
        """
        self.ensure_one()
        struct = self.struct_id
        frequency = struct and struct.ph_pay_frequency or 'monthly'
        deduction_cutoff = struct and struct.ph_deduction_cutoff or 'second'
        split_day = (struct and struct.ph_cutoff_split_day) or 15
        return frequency, deduction_cutoff, split_day

    def _ph_get_cutoff_position(self):
        """'first' or 'second' half of the month, based on the payslip's
        period-end date and the structure's configured split day.
        """
        self.ensure_one()
        _frequency, _deduction_cutoff, split_day = self._ph_get_pay_policy()
        if not self.date_to:
            return 'first'
        return 'first' if self.date_to.day <= split_day else 'second'

    def _ph_get_wage_share(self):
        """Fraction of the monthly contract wage this payslip's Basic
        Salary represents (1.0 for monthly, 0.5 for semi-monthly).
        """
        self.ensure_one()
        frequency, _deduction_cutoff, _split_day = self._ph_get_pay_policy()
        return 1.0 if frequency == 'monthly' else 0.5

    def _ph_get_deduction_share(self):
        """Fraction (0.0, 0.5 or 1.0) of the full monthly government
        contribution/loan amortization that applies to THIS payslip,
        based on the structure's configured policy.
        """
        self.ensure_one()
        frequency, deduction_cutoff, _split_day = self._ph_get_pay_policy()
        if frequency == 'monthly':
            return 1.0
        if deduction_cutoff == 'both':
            return 0.5
        return 1.0 if deduction_cutoff == self._ph_get_cutoff_position() else 0.0

    def _ph_get_loan_deduction_values(self):
        """Return {input_code: amount_due_this_period} for the employee's
        active (running) loans, without touching their balance. The balance
        is only actually decremented once the payslip is confirmed, see
        ``_ph_post_loan_payments``. Amounts are already scaled by the
        structure's configured deduction share for this payslip.
        """
        self.ensure_one()
        values = {}
        if not self.employee_id:
            return values
        share = self._ph_get_deduction_share()
        if not share:
            return values
        loans = self.env['hr.employee.loan'].sudo().search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'running'),
        ])
        for loan in loans:
            code = loan.loan_type_id.code
            due = min(loan.monthly_amortization, loan.balance) * share
            if due > 0:
                values[code] = values.get(code, 0.0) + due
        return values

    def _ph_get_government_contribution_values(self):
        """Return {input_code: amount} for the SSS/PhilHealth/HDMF employee
        and employer shares, based on the contract's full monthly wage and
        already scaled by the structure's configured deduction share for
        this payslip.
        """
        self.ensure_one()
        contract = self._ph_get_contract()
        if not contract:
            return {}
        share = self._ph_get_deduction_share()
        if not share:
            return {}
        sss = contract._get_ph_sss_contribution()
        philhealth = contract._get_ph_philhealth_contribution()
        hdmf = contract._get_ph_hdmf_contribution()
        return {
            'SSSEE': sss['ee_total'] * share,
            'SSSER': sss['er_total'] * share,
            'PHICEE': philhealth['ee'] * share,
            'PHICER': philhealth['er'] * share,
            'HDMFEE': hdmf['ee'] * share,
            'HDMFER': hdmf['er'] * share,
        }

    def _ph_get_worked_days_lines(self):
        """Return this payslip's worked-days/attendance lines, without
        hard-coding the field name (this build has already renamed several
        fields we assumed were stable elsewhere). Returns an empty
        recordset/list if the field can't be found, logging a warning
        rather than raising, since overtime/daily-paid computation is not
        critical-path for the rest of the payslip.
        """
        self.ensure_one()
        for candidate in ('worked_days_line_ids', 'worked_days_lines_ids', 'worked_days_ids'):
            if candidate in self._fields:
                return self[candidate]
        _logger.warning(
            'ph_payroll_extension: could not find a worked-days field on '
            'hr.payslip (tried %s); overtime hours and daily-paid Basic '
            'Salary will compute as 0 until this is resolved.',
            ('worked_days_line_ids', 'worked_days_lines_ids', 'worked_days_ids'))
        return self.env['hr.payslip'].browse()

    def _ph_get_overtime_hours(self):
        """Return {ph.overtime.type record: hours} for this payslip, by
        matching each configured Overtime Type's Work Entry Type code
        against the worked-days lines' own code.
        """
        self.ensure_one()
        result = {}
        ot_types = self.env['ph.overtime.type'].sudo().search([])
        if not ot_types:
            return result
        lines = self._ph_get_worked_days_lines()
        if not lines:
            return result
        hours_by_code = {}
        for line in lines:
            code = getattr(line, 'code', False)
            hours = getattr(line, 'number_of_hours', 0.0) or 0.0
            if code and hours:
                hours_by_code[code] = hours_by_code.get(code, 0.0) + hours
        for ot_type in ot_types:
            hours = hours_by_code.get(ot_type.work_entry_code, 0.0)
            if hours:
                result[ot_type] = hours
        return result

    def _ph_get_worked_days_count(self):
        """Sum of days worked this period, excluding days paid separately
        as Overtime. Used for the Daily-paid Basic Salary formula.
        """
        self.ensure_one()
        lines = self._ph_get_worked_days_lines()
        if not lines:
            return 0.0
        ot_codes = {ot.work_entry_code for ot in self.env['ph.overtime.type'].sudo().search([])}
        total = 0.0
        for line in lines:
            code = getattr(line, 'code', False)
            if code in ot_codes:
                continue
            total += getattr(line, 'number_of_days', 0.0) or 0.0
        return total

    def _ph_get_hourly_rate(self):
        self.ensure_one()
        contract = self._ph_get_contract()
        if not contract:
            return 0.0
        struct = self.struct_id
        divisor = (struct and struct.ph_standard_monthly_hours) or 208.0
        if not divisor:
            return 0.0
        return contract.wage / divisor

    def _ph_get_overtime_value(self):
        self.ensure_one()
        hourly_rate = self._ph_get_hourly_rate()
        if not hourly_rate:
            return 0.0
        total = 0.0
        for ot_type, hours in self._ph_get_overtime_hours().items():
            total += hours * hourly_rate * (ot_type.multiplier / 100.0)
        return total

    def _ph_get_basic_wage_amount(self):
        """Basic Salary for this payslip: monthly-paid prorates the
        contract's monthly wage per the Pay Frequency; daily-paid treats
        the contract wage as a DAILY rate and multiplies by actual days
        worked this period (attendance-based).
        """
        self.ensure_one()
        contract = self._ph_get_contract()
        if not contract:
            return 0.0
        struct = self.struct_id
        treatment = (struct and struct.ph_pay_treatment) or 'monthly_paid'
        if treatment == 'daily_paid':
            return contract.wage * self._ph_get_worked_days_count()
        return contract.wage * self._ph_get_wage_share()

    def _ph_get_input_values(self):
        self.ensure_one()
        values = {
            'BASICWAGE': self._ph_get_basic_wage_amount(),
            'OVERTIME': self._ph_get_overtime_value(),
            'COMMISSION': self.commission_amount,
            'ALLOWTAX': self.total_taxable_allowance,
            'ALLOWNONTAX': self.total_nontaxable_allowance,
        }
        for code, amount in self._ph_get_government_contribution_values().items():
            values[code] = values.get(code, 0.0) + amount
        for code, amount in self._ph_get_loan_deduction_values().items():
            values[code] = values.get(code, 0.0) + amount
        return values

    def _ph_sync_payslip_inputs(self):
        """Push Commission / Allowance / Loan-deduction amounts onto the
        standard ``hr.payslip.input`` lines so the PH salary rules can read
        them through the regular ``inputs.<CODE>.amount`` mechanism.
        """
        input_type_model = self.env['hr.payslip.input.type'].sudo()
        input_line_model = self.env['hr.payslip.input'].sudo()
        input_line_contract_field = None
        for field_name, field in input_line_model._fields.items():
            if getattr(field, 'type', None) == 'many2one' and \
                    getattr(field, 'comodel_name', None) in ('hr.version', 'hr.contract'):
                input_line_contract_field = field_name
                break
        for slip in self:
            slip.overtime_hours = sum(slip._ph_get_overtime_hours().values())
            contract = slip._ph_get_contract()
            if not contract:
                continue
            values = slip._ph_get_input_values()
            lines_by_code = {line.code: line for line in slip.input_line_ids if line.code in values}
            for code, amount in values.items():
                line = lines_by_code.get(code)
                if line:
                    if amount:
                        line.amount = amount
                    else:
                        line.unlink()
                elif amount:
                    input_type = input_type_model.search([('code', '=', code)], limit=1)
                    if not input_type:
                        continue
                    create_vals = {
                        'payslip_id': slip.id,
                        'input_type_id': input_type.id,
                        'name': input_type.name,
                        'code': code,
                        'amount': amount,
                    }
                    # Some Odoo versions require a contract/version reference
                    # on the input line; others don't have one at all.
                    if input_line_contract_field:
                        create_vals[input_line_contract_field] = contract.id
                    try:
                        input_line_model.create(create_vals)
                    except Exception:
                        _logger.warning(
                            'ph_payroll_extension: failed to create a '
                            'hr.payslip.input line for code %s on payslip %s; '
                            'the PH_%s salary rule will compute as 0 for this '
                            'payslip until this is resolved.',
                            code, slip.id, code, exc_info=True)

    def compute_sheet(self):
        self._ph_sync_payslip_inputs()
        return super().compute_sheet()

    def _ph_post_loan_payments(self):
        for slip in self:
            if not slip.employee_id:
                continue
            loans = self.env['hr.employee.loan'].sudo().search([
                ('employee_id', '=', slip.employee_id.id),
                ('state', '=', 'running'),
            ])
            for loan in loans:
                line = slip.line_ids.filtered(lambda l, code=loan.loan_type_id.code: l.code == code)
                amount = abs(line.total) if line else min(loan.monthly_amortization, loan.balance)
                amount = min(amount, loan.balance)
                if amount <= 0:
                    continue
                new_balance = loan.balance - amount
                self.env['hr.employee.loan.payment'].sudo().create({
                    'loan_id': loan.id,
                    'payslip_id': slip.id,
                    'date': slip.date_to,
                    'amount': amount,
                    'balance_after': new_balance,
                })
                loan.balance = new_balance
                if new_balance <= 0:
                    loan.state = 'done'
        self.write({'ph_loans_posted': True})

    def write(self, vals):
        to_post = self.browse()
        if vals.get('state') in ('done', 'paid'):
            to_post = self.filtered(lambda p: p.state not in ('done', 'paid') and not p.ph_loans_posted)
        result = super().write(vals)
        if to_post:
            to_post._ph_post_loan_payments()
        return result
