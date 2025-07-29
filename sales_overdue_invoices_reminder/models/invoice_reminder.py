from odoo import models, fields, api
from datetime import date

class InvoiceReminder(models.Model):
    _inherit = 'account.move'  # Extend the 'account.move' model to access invoices

    @api.model
    def send_overdue_invoice_reminders(self):
        """
        This method searches for all customer invoices that are:
        - posted,
        - overdue,
        - not fully paid,
        and then emails the assigned salesperson (or creator if no salesperson).
        """
        today = date.today()  # Get today's date

        # Find all customer invoices (move_type='out_invoice') that are posted, overdue, and not paid
        overdue_invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date_due', '<', today),
            ('payment_state', '!=', 'paid'),
        ])

        salespersons = {}  # Dictionary to group invoices by salesperson

        for invoice in overdue_invoices:
            # Fallback to creator if no salesperson is assigned
            salesperson = invoice.invoice_user_id or invoice.create_uid

            # Group invoices by salesperson
            if salesperson:
                salespersons.setdefault(salesperson, []).append(invoice)

        # Send email for each salesperson
        for salesperson, invoices in salespersons.items():
            # Build HTML email body
            body = f"Dear {salesperson.name},<br><br>You have the following overdue invoices:<br><ul>"

            for inv in invoices:
                body += (
                    f"<li><strong>{inv.name}</strong> — "
                    f"Customer: {inv.partner_id.name}, "
                    f"Due: {inv.invoice_date_due}, "
                    f"Amount: {inv.amount_total:.2f}</li>"
                )

            body += "</ul><br>Please take the necessary follow-up action.<br><br>Regards,<br>Accounting Team"

            # Prepare and send email
            self.env['mail.mail'].create({
                'subject': 'Overdue Invoice Reminder',
                'body_html': body,
                'email_to': salesperson.email,
                'auto_delete': True,
            }).send()