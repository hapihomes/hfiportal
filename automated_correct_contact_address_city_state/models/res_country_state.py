from odoo import fields, models


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    region_id = fields.Many2one(
        'res.country.region', string='Region',
        domain="[('country_id', '=', country_id)]")
