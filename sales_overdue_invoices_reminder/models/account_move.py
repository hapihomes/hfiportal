from odoo import models, fields, api
from datetime import datetime, timedelta

# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'  # This adds custom logic to existing model

    @api.model
    def send_overdue_invoice_reminders(self):
        """
        Sends an email to each salesperson who has overdue invoices.
        """
        today = fields.Date.today()  # Get today’s date

        # Find all overdue customer invoices (posted and not paid)
        overdue_invoices = self.search([
            ('move_type', '=', 'out_invoice'),  # Only customer invoices
            ('invoice_date_due', '<', today),   # Due date is in the past
            ('payment_state', '!=', 'paid'),    # Still unpaid
            ('state', '=', 'posted'),           # Only posted entries
        ])

        # Group invoices by salesperson
        salesperson_invoices = {}
        for invoice in overdue_invoices:
            salesperson = invoice.invoice_user_id
            if salesperson and salesperson.partner_id.email:
                # Build dictionary by salesperson
                salesperson_invoices.setdefault(salesperson, []).append(invoice)

        # Send an email to each salesperson
        for salesperson, invoices in salesperson_invoices.items():
            # Build HTML email body
            body = "<p>Dear {},</p><p>You have the following overdue invoices:</p><ul>".format(salesperson.name)
            for inv in invoices:
                body += "<li><b>{}</b> for customer <b>{}</b> (Due: {})</li>".format(
                    inv.name, inv.partner_id.name, inv.invoice_date_due)
            body += "</ul><p>Please follow up immediately.</p>"

            # Create and send the email
            self.env['mail.mail'].create({
                'subject': 'Overdue Invoices Reminder',
                'body_html': body,
                'email_to': salesperson.partner_id.email,
            }).send()

        return True

