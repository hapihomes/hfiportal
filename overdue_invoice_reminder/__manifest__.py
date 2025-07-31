{
    "name": "Overdue Invoice Reminder",
    "version": "1.0",
    "summary": "Send email reminders for overdue invoices to Salespersons",
    "depends": ["account", "mail", "base"],
    "data": [
        "data/mail_template.xml",
        "data/cron.xml",
    ],
    "installable": True,
    "application": False,
}
