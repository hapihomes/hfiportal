import re

from odoo import api, fields, models


def normalize_location(text):
    """Uppercase, strip punctuation and collapse whitespace so that
    'Dagupan City', 'dagupan  city.' and 'DAGUPAN CITY' all match."""
    if not text:
        return False
    text = re.sub(r'[^\w\s]', ' ', text, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', text).strip().upper() or False


class DispatchReceiptLine(models.Model):
    _name = 'dispatch.receipt.line'
    _description = 'Dispatch Delivery Receipt Line'
    _order = 'sequence, id'

    dispatch_id = fields.Many2one(
        'dispatch.receipt', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)

    picking_id = fields.Many2one(
        'stock.picking', string='TR/DR#', required=True,
        domain="[('picking_type_code', '=', 'outgoing'), ('state', 'not in', ('draft', 'cancel'))]")
    tr_dr = fields.Char(string='TR/DR#', related='picking_id.name')
    si_ref = fields.Char(
        string='SI#', compute='_compute_si_ref', store=True, readonly=False)
    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        compute='_compute_partner_id', store=True, readonly=False)
    client_name = fields.Char(
        string='Client Name', compute='_compute_client_name', store=True, readonly=False)
    location = fields.Char(
        string='Location', compute='_compute_location', store=True, readonly=False)
    remarks = fields.Char()

    @api.depends('picking_id.sale_id.name')
    def _compute_si_ref(self):
        for line in self:
            line.si_ref = line.picking_id.sale_id.name or False

    @api.depends('picking_id.partner_id')
    def _compute_partner_id(self):
        for line in self:
            line.partner_id = line.picking_id.partner_id

    @api.depends('partner_id')
    def _compute_client_name(self):
        for line in self:
            partner = line.partner_id
            if not partner:
                line.client_name = False
                continue
            # Show the company name plus branch/contact, e.g.
            # "CSI WAREHOUSE CLUB INC - DAGUPAN"
            line.client_name = partner.display_name

    @api.depends('partner_id.city', 'partner_id.state_id')
    def _compute_location(self):
        for line in self:
            partner = line.partner_id
            line.location = normalize_location(
                partner.city or partner.state_id.name) if partner else False
