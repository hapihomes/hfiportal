from odoo import api, fields, models

# Convention: the last (open-ended) bracket must use this as range_to instead
# of leaving it empty, so bracket lookup can always use a plain <= / >= domain.
OPEN_ENDED_CEILING = 999999999.99


class PhSssTable(models.Model):
    _name = 'ph.sss.table'
    _description = 'PH SSS Contribution Bracket'
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
    monthly_salary_credit = fields.Monetary(string='Monthly Salary Credit (MSC)', required=True)

    ee_regular_ss = fields.Monetary(string='Employee Regular SS')
    er_regular_ss = fields.Monetary(string='Employer Regular SS')
    ee_mpf = fields.Monetary(string='Employee MPF/WISP')
    er_mpf = fields.Monetary(string='Employer MPF/WISP')
    er_ec = fields.Monetary(string='Employer EC Contribution')

    ee_total = fields.Monetary(string='Total Employee Share', compute='_compute_totals', store=True)
    er_total = fields.Monetary(string='Total Employer Share', compute='_compute_totals', store=True)
    total_contribution = fields.Monetary(compute='_compute_totals', store=True)

    @api.depends('range_from', 'range_to')
    def _compute_name(self):
        for rec in self:
            rec.name = f'{rec.range_from:,.2f} - {rec.range_to:,.2f}'

    @api.depends('ee_regular_ss', 'ee_mpf', 'er_regular_ss', 'er_mpf', 'er_ec')
    def _compute_totals(self):
        for rec in self:
            rec.ee_total = rec.ee_regular_ss + rec.ee_mpf
            rec.er_total = rec.er_regular_ss + rec.er_mpf + rec.er_ec
            rec.total_contribution = rec.ee_total + rec.er_total

    @api.model
    def _get_contribution(self, wage, company=None):
        """Return the SSS contribution breakdown for the given monthly wage."""
        company = company or self.env.company
        bracket = self.search([
            ('company_id', '=', company.id),
            ('active', '=', True),
            ('range_from', '<=', wage),
            ('range_to', '>=', wage),
        ], order='range_from desc', limit=1)
        if not bracket:
            return {
                'msc': 0.0, 'ee_regular_ss': 0.0, 'er_regular_ss': 0.0,
                'ee_mpf': 0.0, 'er_mpf': 0.0, 'er_ec': 0.0,
                'ee_total': 0.0, 'er_total': 0.0,
            }
        return {
            'msc': bracket.monthly_salary_credit,
            'ee_regular_ss': bracket.ee_regular_ss,
            'er_regular_ss': bracket.er_regular_ss,
            'ee_mpf': bracket.ee_mpf,
            'er_mpf': bracket.er_mpf,
            'er_ec': bracket.er_ec,
            'ee_total': bracket.ee_total,
            'er_total': bracket.er_total,
        }
