from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class DispatchReceipt(models.Model):
    _name = 'dispatch.receipt'
    _description = 'Dispatch Delivery Receipt'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Control #', required=True, copy=False, readonly=True,
        default=lambda self: _('New'))
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Dispatched'),
         ('done', 'Done'), ('cancel', 'Cancelled')],
        default='draft', tracking=True, copy=False)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True)

    date = fields.Date(
        string='Delivery Date', required=True, tracking=True,
        default=fields.Date.context_today)
    carrier_name = fields.Char(string='Transport Provider')

    # Fleet alignment (driver auto-filled from vehicle, still editable for
    # third-party drivers who are not in Fleet)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', tracking=True)
    driver_id = fields.Many2one(
        'res.partner', string='Driver (Fleet)',
        compute='_compute_driver_id', store=True, readonly=False)
    driver_name = fields.Char(
        string="Driver's Name",
        compute='_compute_driver_name', store=True, readonly=False)
    driver_phone = fields.Char(
        string='Driver Contact', compute='_compute_driver_phone',
        store=True, readonly=False)
    helper_names = fields.Char(string='Delivery Helper(s)')

    # Truck details pulled from Fleet (editable for third-party trucks)
    truck_plate = fields.Char(
        string='Plate No.', compute='_compute_truck_details', store=True, readonly=False)
    truck_model = fields.Char(
        string='Truck Model', compute='_compute_truck_details', store=True, readonly=False)
    truck_type = fields.Char(
        string='Truck Type', compute='_compute_truck_details', store=True, readonly=False)
    odometer_departure = fields.Float(
        string='Odometer (Departure)', compute='_compute_truck_details',
        store=True, readonly=False)
    odometer_arrival = fields.Float(string='Odometer (Arrival)')

    delivery_area = fields.Char(
        string='Delivery Area', compute='_compute_delivery_area',
        store=True, readonly=False)

    line_ids = fields.One2many('dispatch.receipt.line', 'dispatch_id', string='Deliveries')

    prepared_by_id = fields.Many2one(
        'hr.employee', string='Prepared By',
        default=lambda self: self.env.user.employee_id)
    approved_by_id = fields.Many2one('hr.employee', string='Approved By')
    dispatched_by_id = fields.Many2one('hr.employee', string='Dispatched By')

    total_customers = fields.Integer(compute='_compute_totals')
    total_pickings = fields.Integer(string='Qty of TR/DR', compute='_compute_totals')
    total_si = fields.Integer(string='Qty of SI', compute='_compute_totals')

    @api.depends('vehicle_id.driver_id')
    def _compute_driver_id(self):
        for rec in self:
            if rec.vehicle_id:
                rec.driver_id = rec.vehicle_id.driver_id
            elif not rec.driver_id:
                rec.driver_id = False

    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        """Reverse direction: pick a driver first and find their Fleet vehicle."""
        if self.driver_id and not self.vehicle_id:
            vehicle = self.env['fleet.vehicle'].search(
                [('driver_id', '=', self.driver_id.id)], limit=1)
            if vehicle:
                self.vehicle_id = vehicle

    @api.depends('driver_id')
    def _compute_driver_phone(self):
        for rec in self:
            rec.driver_phone = (
                rec.driver_id.phone if rec.driver_id else rec.driver_phone)

    @api.depends('vehicle_id')
    def _compute_truck_details(self):
        for rec in self:
            v = rec.vehicle_id
            if not v:
                continue
            rec.truck_plate = v.license_plate
            rec.truck_model = v.model_id.display_name
            rec.truck_type = v.category_id.name if 'category_id' in v._fields else False
            rec.odometer_departure = v.odometer

    @api.depends('driver_id')
    def _compute_driver_name(self):
        for rec in self:
            if rec.driver_id:
                rec.driver_name = rec.driver_id.name
            elif not rec.driver_name:
                rec.driver_name = False

    @api.depends('line_ids.location')
    def _compute_delivery_area(self):
        for rec in self:
            areas = []
            for loc in rec.line_ids.mapped('location'):
                if loc and loc not in areas:
                    areas.append(loc)
            rec.delivery_area = ' / '.join(areas) if areas else False

    @api.depends('line_ids.partner_id', 'line_ids.picking_id', 'line_ids.si_ref')
    def _compute_totals(self):
        for rec in self:
            rec.total_customers = len(rec.line_ids.mapped('partner_id'))
            rec.total_pickings = len(rec.line_ids.filtered('picking_id'))
            rec.total_si = len(rec.line_ids.filtered('si_ref'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                date = vals.get('date') or fields.Date.context_today(self)
                vals['name'] = self.env['ir.sequence'].with_context(
                    ir_sequence_date=date).next_by_code('dispatch.receipt') or _('New')
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Add at least one delivery order before dispatching.'))
        self.state = 'confirmed'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    def action_print(self):
        return self.env.ref(
            'dispatch_delivery_receipt.action_report_dispatch_receipt').report_action(self)

    @api.constrains('line_ids')
    def _check_picking_unique(self):
        for rec in self:
            pickings = rec.line_ids.picking_id
            if len(pickings) != len(rec.line_ids.filtered('picking_id')):
                raise ValidationError(_('A delivery order can only appear once per dispatch.'))
            other = self.env['dispatch.receipt.line'].search([
                ('picking_id', 'in', pickings.ids),
                ('dispatch_id', '!=', rec.id),
                ('dispatch_id.state', '!=', 'cancel'),
            ], limit=1)
            if other:
                raise ValidationError(_(
                    '%(picking)s is already on dispatch %(dispatch)s.',
                    picking=other.picking_id.name, dispatch=other.dispatch_id.name))

    # ------------------------------------------------------------------
    # Report helper: lines sorted so same-location stops are grouped
    # ------------------------------------------------------------------
    def _get_sorted_lines(self):
        self.ensure_one()
        return self.line_ids.sorted(
            key=lambda l: ((l.location or '~'), (l.client_name or ''), l.sequence, l.id))
