"""
Stock Ageing Report - core model
================================

HOW THE REPORT WORKS (big picture)
----------------------------------
1. `_refresh()` deletes the old snapshot rows and rebuilds them.
2. For every company, `_compute_company_rows()`:
     a. finds the locations we report on (internal, not consignment),
     b. reads what is physically on hand now (stock.quant),
     c. replays the WHOLE history of done stock move lines (since the start
        of the database) to know, for each unit on hand, the date it came in
        (FIFO "layers"),
     d. turns every layer into one report row with its age and age bucket.
3. The rows are stored in this model (stock.ageing.report) so the pivot,
   list, Excel, CSV and PDF outputs all read the same saved snapshot.
   The heavy step (2c) runs only on "Recompute" or from the nightly cron.
"""
from collections import defaultdict

from odoo import api, fields, models

# Age given to products that were never sold (business rule A).
NO_SALE_AGE = 365


class StockAgeingReport(models.Model):
    _name = 'stock.ageing.report'
    _description = 'Stock Ageing Report'
    _order = 'location_id, product_id, in_date'

    # ---- Dimensions (used as pivot rows / filters) ----------------------
    product_id = fields.Many2one('product.product', readonly=True, index=True)
    categ_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    location_id = fields.Many2one('stock.location', readonly=True, index=True)
    warehouse_id = fields.Many2one('stock.warehouse', readonly=True)
    company_id = fields.Many2one('res.company', readonly=True, index=True)

    # Date the units entered the stock location. Grouping the pivot by this
    # date gives the Year / Quarter / Month / Day breakdown.
    in_date = fields.Date(string='In Stock Since', readonly=True)
    age_days = fields.Integer(string='Age (Days)', readonly=True, aggregator='avg')
    no_sale = fields.Boolean(string='Never Sold', readonly=True)

    # ---- Measures --------------------------------------------------------
    quantity = fields.Float(string='Quantity', readonly=True)
    value = fields.Float(string='Value', readonly=True)  # quantity x standard price

    # One column per age bucket. Each row fills exactly ONE of them
    # (the others stay 0), so summing a column in the pivot gives the total
    # quantity that sits in that bucket.
    qty_0_30 = fields.Float(string='0 - 30 Days', readonly=True)
    qty_30_90 = fields.Float(string='30 - 90 Days', readonly=True)
    qty_90_180 = fields.Float(string='90 - 180 Days', readonly=True)
    qty_180_365 = fields.Float(string='180 - 365 Days', readonly=True)
    qty_365_plus = fields.Float(string='365+ Days', readonly=True)

    # Names of the bucket fields, used when exporting.
    BUCKETS = ['qty_0_30', 'qty_30_90', 'qty_90_180', 'qty_180_365', 'qty_365_plus']

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------
    @api.model
    def _cron_refresh(self):
        """Called by the nightly scheduled action: rebuild for ALL companies."""
        companies = self.env['res.company'].sudo().search([])
        # `allowed_company_ids` makes `self.env.companies` return every company.
        self.with_context(allowed_company_ids=companies.ids)._refresh()

    @api.model
    def _refresh(self):
        """Throw away the old snapshot and rebuild it for the active companies."""
        companies = self.env.companies
        # sudo(): warehouse users only have READ access on this model,
        # but the rebuild has to create/delete rows.
        Report = self.sudo().env['stock.ageing.report']
        Report.search([('company_id', 'in', companies.ids)]).unlink()

        vals_list = []
        for company in companies:
            vals_list += self._compute_company_rows(company)
        if vals_list:
            Report.create(vals_list)  # one batch create = much faster than row by row

    # ------------------------------------------------------------------
    # Age bucket
    # ------------------------------------------------------------------
    @api.model
    def _bucket(self, age):
        """Return the name of the bucket field an age (in days) belongs to."""
        if age <= 30:
            return 'qty_0_30'
        if age <= 90:
            return 'qty_30_90'
        if age <= 180:
            return 'qty_90_180'
        if age < 365:
            return 'qty_180_365'
        return 'qty_365_plus'  # 365 and older (never-sold stock lands here)

    # ------------------------------------------------------------------
    # Main computation (one company)
    # ------------------------------------------------------------------
    @api.model
    def _compute_company_rows(self, company):
        """Return a list of `create()` value dicts, one per FIFO layer."""
        env = self.sudo().with_company(company).env
        cr = env.cr
        today = fields.Date.context_today(self)

        # ---- Step a: which locations do we report on? --------------------
        # Only internal locations, and never consignment ones.
        # Customer / supplier / virtual locations are not internal, so they
        # are automatically outside the report.
        locations = env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('is_consignment', '=', False),
            ('company_id', 'in', [company.id, False]),
        ])
        # {location id: warehouse id}. Also acts as the "is this location
        # tracked?" lookup (`loc_id in loc_wh`).
        loc_wh = {loc.id: loc.warehouse_id.id for loc in locations}
        if not loc_wh:
            return []

        # ---- Step b: what is on hand right now? --------------------------
        # Sum of quants per (product, location), plus the oldest quant date
        # (used later only as a fallback date).
        quant_data = env['stock.quant']._read_group(
            [('location_id', 'in', locations.ids), ('company_id', '=', company.id)],
            ['product_id', 'location_id'],
            ['quantity:sum', 'in_date:min'],
        )
        # target[(product_id, location_id)] = (on-hand qty, oldest quant date)
        target = {}
        for product, location, qty, min_in_date in quant_data:
            if qty > 0:
                target[(product.id, location.id)] = (qty, min_in_date)
        if not target:
            return []
        product_ids = list({p for p, _l in target})

        # ---- Rule A: which products were EVER sold? ----------------------
        # "Sold" = at least one done move line going to a customer location.
        cr.execute("""
            SELECT DISTINCT sml.product_id
              FROM stock_move_line sml
              JOIN stock_location dest ON dest.id = sml.location_dest_id
             WHERE sml.state = 'done'
               AND dest.usage = 'customer'
               AND sml.product_id = ANY(%s)
        """, [product_ids])
        sold = {r[0] for r in cr.fetchall()}

        # ---- Step c: FIFO replay of the full move history ----------------
        # Every done move line of the products we care about, oldest first,
        # from the very first move in the database.
        cr.execute("""
            SELECT product_id, location_id, location_dest_id, date, quantity_product_uom
              FROM stock_move_line
             WHERE state = 'done'
               AND product_id = ANY(%s)
               AND quantity_product_uom > 0
               AND location_id != location_dest_id
             ORDER BY date, id
        """, [product_ids])

        # layers[(product, location)] = [[date_in, qty], ...] sorted oldest first.
        # Think of it as a queue of "batches" waiting in that location.
        layers = defaultdict(list)
        for pid, src, dst, dt, qty in cr.fetchall():
            src_in = src in loc_wh   # does the move leave a tracked location?
            dst_in = dst in loc_wh   # does the move enter a tracked location?
            if not src_in and not dst_in:
                continue  # happened entirely outside the report, ignore

            day = dt.date()

            # 1) Where do the moved units come from?
            if src_in:
                # Leaving a tracked location: FIFO takes the OLDEST batches first.
                consumed = self._consume(layers[(pid, src)], qty)
            else:
                # Coming from outside (supplier receipt, customer RETURN,
                # inventory adjustment, consignment return, production...):
                # this is a brand-new batch dated today. This is what makes a
                # returned item start again at 0 days (rule C).
                consumed = [[day, qty]]

            # 2) Where do they go?
            if dst_in:
                same_wh = src_in and loc_wh[src] and loc_wh[src] == loc_wh[dst]
                if not same_wh:
                    # Entering the warehouse (or a different warehouse):
                    # the ageing clock starts at this move's date.
                    consumed = [[day, q] for _d, q in consumed] or [[day, qty]]
                # else: internal transfer inside the same warehouse -> the
                # batches keep their ORIGINAL dates (age is not reset).
                dest_layers = layers[(pid, dst)]
                dest_layers.extend(consumed)
                dest_layers.sort(key=lambda l: l[0])  # keep oldest first
            # If the destination is not tracked (customer, consignment...),
            # the consumed batches simply disappear from our queues.

        # ---- Step d: build one report row per remaining batch ------------
        products = env['product.product'].browse(product_ids)
        cost = {p.id: p.standard_price for p in products}
        categ = {p.id: p.categ_id.id for p in products}

        vals_list = []
        for (pid, lid), (qty, min_in_date) in target.items():
            # The replay can drift from reality (old data, manual quant edits).
            # Force the layers to add up to the real on-hand quantity.
            pair_layers = self._reconcile(
                layers.get((pid, lid), []), qty,
                (min_in_date and min_in_date.date()) or today)

            # Rule A: never sold -> the whole stock is 365 days old,
            # wherever it is (single layer dated exactly 365 days ago).
            no_sale = pid not in sold
            if no_sale:
                pair_layers = [[fields.Date.subtract(today, days=NO_SALE_AGE), qty]]

            for day, lqty in pair_layers:
                age = (today - day).days
                vals = {
                    'product_id': pid,
                    'categ_id': categ[pid],
                    'location_id': lid,
                    'warehouse_id': loc_wh[lid] or False,
                    'company_id': company.id,
                    'in_date': day,
                    'age_days': age,
                    'no_sale': no_sale,
                    'quantity': lqty,
                    'value': lqty * cost[pid],
                    # all buckets start at 0 ...
                    'qty_0_30': 0.0, 'qty_30_90': 0.0, 'qty_90_180': 0.0,
                    'qty_180_365': 0.0, 'qty_365_plus': 0.0,
                }
                # ... and the matching one receives the quantity.
                vals[self._bucket(age)] = lqty
                vals_list.append(vals)
        return vals_list

    # ------------------------------------------------------------------
    # FIFO helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _consume(pair_layers, qty):
        """Remove `qty` units from the OLDEST batches of a queue (FIFO).

        `pair_layers` is modified in place. Returns the batches that were
        taken, as [[date, qty], ...], so they can be moved to another location.
        Example: queue [[Jan,5],[Mar,10]], consume 7 -> returns [[Jan,5],[Mar,2]]
        and the queue becomes [[Mar,8]].
        """
        taken = []
        while qty > 1e-9 and pair_layers:
            day, lqty = pair_layers[0]
            if lqty <= qty + 1e-9:
                # the whole oldest batch is used up
                taken.append([day, lqty])
                qty -= lqty
                pair_layers.pop(0)
            else:
                # only part of the oldest batch is used
                taken.append([day, qty])
                pair_layers[0][1] = lqty - qty
                qty = 0
        return taken

    @staticmethod
    def _reconcile(pair_layers, qty, fallback_day):
        """Make the layers add up to the real on-hand quantity `qty`.

        * Too little in the layers -> add the missing units as a batch dated
          `fallback_day` (oldest quant date), placed first (oldest).
        * Too much in the layers -> drop the excess from the oldest batches.
        """
        layers = [list(l) for l in pair_layers if l[1] > 1e-9]  # work on a copy
        total = sum(l[1] for l in layers)
        if total < qty - 1e-9:
            layers.insert(0, [fallback_day, qty - total])
        elif total > qty + 1e-9:
            excess = total - qty
            while excess > 1e-9 and layers:
                if layers[0][1] <= excess + 1e-9:
                    excess -= layers.pop(0)[1]
                else:
                    layers[0][1] -= excess
                    excess = 0
        return layers

    # ------------------------------------------------------------------
    # Export helper (Excel / CSV / PDF)
    # ------------------------------------------------------------------
    def _export_lines(self):
        """Collapse the layer rows into ONE line per warehouse/location/product.

        Returns a list of dicts with the columns the exports need. The
        recordset is sorted first so the output is ordered nicely.
        """
        grouped = {}
        for rec in self.sorted(lambda r: (r.warehouse_id.name or '',
                                          r.location_id.complete_name or '',
                                          r.product_id.display_name or '')):
            key = (rec.warehouse_id, rec.location_id, rec.product_id)
            # first time we see this key: create the line with zeros
            line = grouped.setdefault(key, {
                'warehouse': rec.warehouse_id.name or '',
                'location': rec.location_id.complete_name or '',
                'code': rec.product_id.default_code or '',
                'product': rec.product_id.name or '',
                'never_sold': rec.no_sale,
                'quantity': 0.0, 'value': 0.0,
                **{b: 0.0 for b in self.BUCKETS},
            })
            # then add this layer's numbers to the line
            line['quantity'] += rec.quantity
            line['value'] += rec.value
            for b in self.BUCKETS:
                line[b] += rec[b]
        return list(grouped.values())
