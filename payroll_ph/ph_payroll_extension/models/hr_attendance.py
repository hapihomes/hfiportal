import pytz

from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    currency_id = fields.Many2one(related='employee_id.company_id.currency_id')

    ph_scheduled_time_in = fields.Float(
        string='Scheduled Time In', compute='_compute_ph_lateness', store=True,
        help="The employee's assigned PH Work Schedule Time In, for reference.")
    ph_late_minutes = fields.Float(
        string='Late (Minutes)', compute='_compute_ph_lateness', store=True,
        help='Minutes between the scheduled Time In and the actual check-in, if positive.')
    ph_is_late = fields.Boolean(
        string='Late (Beyond Grace)', compute='_compute_ph_lateness', store=True,
        help="True when Late (Minutes) exceeds the assigned Work Schedule's grace period. "
             'Only records flagged here are pulled into payroll as a deduction.')
    ph_late_deduction = fields.Monetary(
        string='Late Deduction', compute='_compute_ph_lateness', store=True,
        help='Amount deducted from payroll for this late arrival: the full late duration '
             "(not just the minutes beyond the grace period) x the employee's hourly rate "
             '(contract wage / the Work Schedule\'s Standard Monthly Hours).')

    def _ph_get_contract(self):
        """Return the employee's current Contract/Version record, without
        hard-coding a field name (same pattern/rationale as
        HrPayslip._ph_get_contract in hr_payslip.py: this build's Contract
        model is 'hr.version', not the historical 'hr.contract', and the
        exact field name on hr.employee is not assumed stable).
        """
        self.ensure_one()
        employee = self.employee_id
        if not employee:
            return self.env['hr.version']
        for field_name, field in employee._fields.items():
            if getattr(field, 'type', None) == 'many2one' and \
                    getattr(field, 'comodel_name', None) in ('hr.version', 'hr.contract'):
                contract = employee[field_name]
                if contract:
                    return contract
        return self.env['hr.version']

    @api.depends('check_in', 'employee_id')
    def _compute_ph_lateness(self):
        for att in self:
            att.ph_scheduled_time_in = 0.0
            att.ph_late_minutes = 0.0
            att.ph_is_late = False
            att.ph_late_deduction = 0.0
            if not att.check_in or not att.employee_id:
                continue
            contract = att._ph_get_contract()
            schedule = contract.ph_work_schedule_id if contract else False
            if not schedule:
                continue

            tz_name = att.employee_id.tz or self.env.user.tz or 'UTC'
            try:
                tz = pytz.timezone(tz_name)
            except Exception:
                tz = pytz.utc
            check_in_local = pytz.utc.localize(att.check_in).astimezone(tz)
            actual_time_in = (
                check_in_local.hour + check_in_local.minute / 60.0 + check_in_local.second / 3600.0)

            att.ph_scheduled_time_in = schedule.time_in
            late_minutes = (actual_time_in - schedule.time_in) * 60.0
            if late_minutes <= 0:
                continue
            att.ph_late_minutes = late_minutes
            if late_minutes > schedule.grace_period_minutes:
                att.ph_is_late = True
                hourly_rate = contract._get_ph_hourly_rate()
                att.ph_late_deduction = (late_minutes / 60.0) * hourly_rate
