from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools import format_date, format_amount
from io import StringIO

class AccountMove(models.Model):
    _inherit = 'account.move'

    def send_overdue_invoice_reminders(self):
        # Find overdue posted customer invoices
        overdue_invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('invoice_date_due', '<', fields.Date.today()),
            ('payment_state', '!=', 'paid'),
            ('state', '=', 'posted'),
            ('user_id', '!=', False),
        ])

        if not overdue_invoices:
            return

        # Group invoices by salesperson
        grouped = {}
        for inv in overdue_invoices:
            grouped.setdefault(inv.user_id, []).append(inv)

        for salesperson, invoices in grouped.items():
            if not salesperson.email:
                continue

            # Build HTML table
            rows_html = ""
            for inv in invoices:
                order_ref = ', '.join(inv.invoice_origin or '-')  # Related SO
                customer_name = inv.partner_id.name or '-'
                invoice_ref = inv.name or '-'
                due_date = format_date(self.env, inv.invoice_date_due, date_format='MMM dd, yyyy')
                amount = format_amount(self.env, inv.amount_total, inv.currency_id)

                rows_html += f"""
                <tr>
                    <td style="padding:5px;border:1px solid #ccc;">{order_ref}</td>
                    <td style="padding:5px;border:1px solid #ccc;">{invoice_ref}</td>
                    <td style="padding:5px;border:1px solid #ccc;">{customer_name}</td>
                    <td style="padding:5px;border:1px solid #ccc;">{due_date}</td>
                    <td style="padding:5px;border:1px solid #ccc;text-align:right;">{amount}</td>
                </tr>
                """

            email_body = f"""
            <p>Dear {salesperson.name},</p>
            <p>Here is a summary of your overdue invoices:</p>
            <table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">
                <thead>
                    <tr style="background-color:#f2f2f2;">
                        <th style="padding:5px;border:1px solid #ccc;">Sales Order Reference</th>
                        <th style="padding:5px;border:1px solid #ccc;">Invoice Reference</th>
                        <th style="padding:5px;border:1px solid #ccc;">Customer Name</th>
                        <th style="padding:5px;border:1px solid #ccc;">Invoice Due Date</th>
                        <th style="padding:5px;border:1px solid #ccc;">Total Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            <p>Kindly follow up with the respective clients.</p>
            <p>Best regards,<br/>Accounting Team</p>
            """

            self.env['mail.mail'].create({
                'subject': _('Overdue Invoices Reminder'),
                'body_html': email_body,
                'email_to': salesperson.email,
                'email_from': self.env.user.email or 'no-reply@yourcompany.com',
            }).send()
