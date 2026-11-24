from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_create_dispatch(self):
        """Create one dispatch receipt from the selected delivery orders."""
        pickings = self.filtered(lambda p: p.picking_type_code == 'outgoing')
        if not pickings:
            raise UserError(_('Select at least one delivery order.'))
        dispatch = self.env['dispatch.receipt'].create({
            'line_ids': [(0, 0, {'picking_id': p.id}) for p in pickings],
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dispatch.receipt',
            'res_id': dispatch.id,
            'view_mode': 'form',
        }
