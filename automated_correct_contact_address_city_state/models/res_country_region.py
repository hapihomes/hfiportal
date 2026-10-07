from odoo import fields, models


class ResCountryRegion(models.Model):
    _name = 'res.country.region'
    _description = 'Country Region'
    _order = 'country_id, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char()
    country_id = fields.Many2one('res.country', required=True, ondelete='cascade')
    state_ids = fields.One2many('res.country.state', 'region_id', string='States')
