from odoo import fields, models


class StockLocation(models.Model):
    # _inherit (without _name) EXTENDS the existing stock.location model.
    _inherit = 'stock.location'

    # Tick this on consignment locations. The ageing engine skips them.
    is_consignment = fields.Boolean(
        string='Consignment Location',
        help='Stock in this location is excluded from the Ageing Products report.',
    )
