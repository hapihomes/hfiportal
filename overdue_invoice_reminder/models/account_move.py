from odoo import models, fields, api
from datetime import date

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def send_overdue_invoice_reminders(self):
        today = date.today()
        invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date_due', '<', today),
            ('payment_state', '!=', 'paid')
        ])

        template = self.env.ref('overdue_invoice_reminder.email_template_overdue_invoice_reminder', raise_if_not_found=False)
        if not template:
            return

        salespersons = {}
        for invoice in invoices:
            if invoice.invoice_user_id:
                salespersons.setdefault(invoice.invoice_user_id, []).append(invoice)

        for user, user_invoices in salespersons.items():
            ctx = {
                'user': user,
                'invoices': user_invoices,
            }
            template.with_context(ctx).send_mail(user.id, force_send=True)
