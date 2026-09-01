from odoo import api, fields, models


class PhPhilhealthConfig(models.Model):
    _name = 'ph.philhealth.config'
    _description = 'PH PhilHealth Contribution Configuration'
    _order = 'date_from desc'

    name = fields.Char(required=True, default='PhilHealth Contribution Rate')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    active = fields.Boolean(default=True)

    date_from = fields.Date(required=True, default=fields.Date.context_today)
    date_to = fields.Date()

    premium_rate = fields.Float(
        string='Total Premium Rate (%)', required=True, default=5.0,
        help='Total PhilHealth premium rate as a percentage of monthly basic salary.')
    ee_share_rate = fields.Float(
        string='Employee Share of Premium (%)', required=True, default=50.0,
        help='Percentage of the total premium charged to the employee. The remainder is the employer share.')

    salary_floor = fields.Monetary(string='Monthly Salary Floor', default=10000.0)
    salary_ceiling = fields.Monetary(string='Monthly Salary Ceiling', default=100000.0)

    @api.model
    def _get_contribution(self, wage, date=None, company=None):
        company = company or self.env.company
        date = date or fields.Date.context_today(self)
        config = self.search([
            ('company_id', '=', company.id),
            ('active', '=', True),
            ('date_from', '<=', date),
            '|', ('date_to', '=', False), ('date_to', '>=', date),
        ], order='date_from desc', limit=1)
        if not config:
            return {'basis': 0.0, 'ee': 0.0, 'er': 0.0, 'total': 0.0}
        basis = min(max(wage, config.salary_floor), config.salary_ceiling)
        total = basis * config.premium_rate / 100.0
        ee = total * config.ee_share_rate / 100.0
        er = total - ee
        return {'basis': basis, 'ee': ee, 'er': er, 'total': total}
