import logging
import re
import unicodedata

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

ADDRESS_TRIGGER_FIELDS = {'street', 'street2', 'city', 'zip', 'country_id', 'state_id'}


def _norm(text):
    """Lowercase, strip accents/punctuation and collapse whitespace."""
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).lower()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', text).split())


def _name_variants(name):
    """Names an address may use for a place, e.g. "Makati City" -> "makati"."""
    base = _norm(name)
    variants = {base}
    for prefix in ('city of ', 'municipality of '):
        if base.startswith(prefix):
            variants.add(base[len(prefix):])
    for suffix in (' city', ' municipality'):
        if base.endswith(suffix):
            variants.add(base[:-len(suffix)])
    return {v for v in variants if v}


def _find_matches(text, records):
    """Return the records whose name appears as whole words in ``text``.

    Only the matches with the longest matched name are kept, so that
    "Quezon City" wins over "Quezon".
    """
    padded = f' {text} '
    best_len, best = 0, []
    for record in records:
        for variant in _name_variants(record.name):
            if f' {variant} ' in padded:
                if len(variant) > best_len:
                    best_len, best = len(variant), [record]
                elif len(variant) == best_len and record not in best:
                    best.append(record)
                break
    return best


class ResPartner(models.Model):
    _inherit = 'res.partner'

    region_id = fields.Many2one(
        'res.country.region', string='Region', ondelete='restrict',
        domain="[('country_id', '=?', country_id)]")

    @api.model
    def _address_fields(self):
        return super()._address_fields() + ['region_id']

    # ------------------------------------------------------------------
    # Address scanning
    # ------------------------------------------------------------------
    def _get_address_autofill_vals(self, cities_by_country=None, states_by_country=None):
        """Scan the address of ``self`` and return the values to write."""
        self.ensure_one()
        cities_by_country = {} if cities_by_country is None else cities_by_country
        states_by_country = {} if states_by_country is None else states_by_country

        text = _norm(' '.join(filter(None, [self.street, self.street2, self.city])))
        country = self.country_id or self.env.company.country_id
        state = self.state_id
        city = self.env['res.country.city']
        vals = {}

        def country_records(cache, model, country):
            key = country.id
            if key not in cache:
                domain = [('country_id', '=', country.id)] if country else []
                cache[key] = self.env[model].sudo().search(domain)
            return cache[key]

        # 1. City: from the text, or from the ZIP code.
        if text or self.zip:
            candidates = country_records(cities_by_country, 'res.country.city', country)
            if state:
                candidates = candidates.filtered(lambda c: c.state_id == state)
            found = _find_matches(text, candidates) if text else []
            if len(found) != 1 and self.zip:
                by_zip = candidates.filtered(lambda c: c.zipcode and c.zipcode == self.zip.strip())
                found = [c for c in found if c in by_zip] or list(by_zip)
            if len(found) == 1:
                city = found[0]
                if not self.city:
                    vals['city'] = city.name

        # 2. State: from the city, or from the text.
        if not state:
            if city and city.state_id:
                state = city.state_id
            elif text:
                found = _find_matches(text, country_records(states_by_country, 'res.country.state', country))
                if len(found) == 1:
                    state = found[0]
            if state:
                vals['state_id'] = state.id

        # 3. Country: from the state.
        if state and not self.country_id and state.country_id:
            vals['country_id'] = state.country_id.id

        # 4. Region: always derived from the state.
        if state and state.region_id and self.region_id != state.region_id:
            vals['region_id'] = state.region_id.id

        return vals

    def _autofill_address(self):
        """Fill Region, City and State of the partners from their address."""
        cities_by_country, states_by_country = {}, {}
        for partner in self:
            vals = partner._get_address_autofill_vals(cities_by_country, states_by_country)
            if not vals:
                continue
            try:
                with self.env.cr.savepoint():
                    partner.with_context(skip_address_autofill=True).write(vals)
            except ValidationError as e:
                # e.g. an invalid VAT that is only checked once the country is set
                _logger.warning("Address auto-fill skipped for partner %s (%s): %s",
                                partner.display_name, partner.id, e)

    # ------------------------------------------------------------------
    # Triggers
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        if not self.env.context.get('skip_address_autofill'):
            partners._autofill_address()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if ADDRESS_TRIGGER_FIELDS & set(vals) and not self.env.context.get('skip_address_autofill'):
            self._autofill_address()
        return res

    @api.onchange('street', 'street2', 'city', 'zip')
    def _onchange_autofill_address(self):
        for partner in self:
            for fname, value in partner._get_address_autofill_vals().items():
                partner[fname] = value

    # ------------------------------------------------------------------
    # Mass action / cron
    # ------------------------------------------------------------------
    def action_autofill_address(self):
        self._autofill_address()
        return True

    @api.model
    def _cron_autofill_address(self, batch_size=500):
        """Fill the partners that have an address but a missing Region/City/State."""
        domain = [
            '|', ('street', '!=', False), '|', ('street2', '!=', False), ('city', '!=', False),
            '|', ('state_id', '=', False), ('region_id', '=', False),
        ]
        self.with_context(active_test=False).search(domain, limit=batch_size)._autofill_address()
