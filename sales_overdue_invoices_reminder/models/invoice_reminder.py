""" from odoo import models, fields, api 
from datetime import date 

class InvoiceReminder(models.Model):
    _inherit = 'account.move'

    @api.model 
    def send_overdue_invoice_reminders """