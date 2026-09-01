from odoo import api, fields, models


class PhHdmfTable(models.Model):
    _name = 'ph.hdmf.table'
    _description = 'PH HDMF (Pag-IBIG) Contribution Bracket'
    _order = 'range_from asc'

    name = fields.Char(compute='_compute_name', store=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    active = fields.Boolean(default=True)
    effective_date = fields.Date(default=fields.Date.context_today)

    range_from = fields.Monetary(string='Salary Range From', required=True)
    range_to = fields.Monetary(
        string='Salary Range To', required=True,
        help='For the top, open-ended bracket use a very high value '
             '(e.g. 999999999.99) instead of leaving it at 0.')
    ee_rate = fields.Float(string='Employee Rate (%)', required=True)
    er_rate = fields.Float(string='Employer Rate (%)', required=True)
    salary_base_cap = fields.Monetary(
        string='Monthly Fund Salary Base Cap', required=True,
        help='The monthly compensation is capped at this amount before the '
             'rates are applied (the "Monthly Fund Salary" base).')

    @api.depends('range_from', 'range_to')
    def _compute_name(self):
        for rec in self:
            rec.name = f'{rec.range_from:,.2f} - {rec.range_to:,.2f}'

    @api.model
    def _get_contribution(self, wage, company=None):
        company = company or self.env.company
        bracket = self.search([
            ('company_id', '=', company.id),
            ('active', '=', True),
            ('range_from', '<=', wage),
            ('range_to', '>=', wage),
        ], order='range_from desc', limit=1)
        if not bracket:
            return {'basis': 0.0, 'ee': 0.0, 'er': 0.0, 'total': 0.0}
        basis = min(wage, bracket.salary_base_cap)
        ee = basis * bracket.ee_rate / 100.0
        er = basis * bracket.er_rate / 100.0
        return {'basis': basis, 'ee': ee, 'er': er, 'total': ee + er}
