from odoo import api, fields, models

from ..data.ph_cities import PH_CITIES, PH_STATE_ALIASES
from ..hooks import _norm


class ResCountryCity(models.Model):
    _name = 'res.country.city'
    _description = 'Country City'
    _order = 'country_id, state_id, name'

    name = fields.Char(required=True, translate=True)
    zipcode = fields.Char()
    country_id = fields.Many2one('res.country', required=True, ondelete='cascade')
    state_id = fields.Many2one(
        'res.country.state', string='State', ondelete='cascade',
        domain="[('country_id', '=', country_id)]")

    @api.model
    def _load_ph_cities(self, *args):
        """Create the missing Philippine cities (idempotent, runs on every upgrade)."""
        country = self.env.ref('base.ph', raise_if_not_found=False)
        if not country:
            return
        states = self.env['res.country.state'].search([('country_id', '=', country.id)])
        state_by_name = {_norm(state.name): state for state in states}
        existing = {(c.name, c.state_id.id) for c in self.search([('country_id', '=', country.id)])}

        vals_list = []
        for key, cities in PH_CITIES.items():
            state = next(
                (state_by_name[n] for n in map(_norm, PH_STATE_ALIASES.get(key, [key]))
                 if n in state_by_name), self.env['res.country.state'])
            for name in cities:
                if (name, state.id) not in existing:
                    vals_list.append({'name': name, 'country_id': country.id, 'state_id': state.id})
        if vals_list:
            self.create(vals_list)
