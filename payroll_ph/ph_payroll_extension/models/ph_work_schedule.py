from odoo import api, fields, models
from odoo.exceptions import UserError


class PhWorkSchedule(models.Model):
    _name = 'ph.work.schedule'
    _description = 'PH Work Schedule / Shift'
    _order = 'time_in, id'

    name = fields.Char(required=True, help='e.g. "Morning Shift (8:00 AM - 5:00 PM)".')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    time_in = fields.Float(
        string='Time In', required=True, default=8.0,
        help='Scheduled shift start time (24h), e.g. 8.5 for 8:30 AM. Same-day shifts only.')
    time_out = fields.Float(
        string='Time Out', required=True, default=17.0,
        help='Scheduled shift end time (24h), e.g. 17.0 for 5:00 PM. Same-day shifts only.')
    break_duration = fields.Float(
        string='Break Duration (Hours)', default=1.0,
        help='Unpaid break subtracted from the shift span to get actual working hours.')
    working_hours = fields.Float(
        string='Working Hours/Day', compute='_compute_working_hours', store=True,
        help='(Time Out - Time In) - Break Duration.')

    grace_period_minutes = fields.Integer(
        string='Grace Period (Minutes)', default=5, required=True,
        help='A clock-in up to this many minutes after Time In is not considered late. '
             'Beyond the grace period, the employee is late for the FULL duration between '
             'Time In and the actual clock-in (not just the minutes past the grace period).')
    standard_monthly_hours = fields.Float(
        string='Standard Monthly Hours', default=208.0, required=True,
        help='Contract wage divided by this number gives the hourly rate used to compute '
             'the late deduction, e.g. 8 hours/day x 26 days/month = 208.')

    @api.depends('time_in', 'time_out', 'break_duration')
    def _compute_working_hours(self):
        for rec in self:
            rec.working_hours = max(rec.time_out - rec.time_in - rec.break_duration, 0.0)

    @api.constrains('time_in', 'time_out', 'break_duration')
    def _check_ph_work_schedule_times(self):
        for rec in self:
            if rec.time_out <= rec.time_in:
                raise UserError(self.env._(
                    'Time Out must be later than Time In (overnight shifts spanning '
                    'midnight are not supported).'))
            if rec.break_duration < 0:
                raise UserError(self.env._('Break Duration cannot be negative.'))
            if (rec.time_out - rec.time_in) <= rec.break_duration:
                raise UserError(self.env._(
                    'Break Duration cannot be greater than or equal to the shift span '
                    '(Time Out - Time In).'))
