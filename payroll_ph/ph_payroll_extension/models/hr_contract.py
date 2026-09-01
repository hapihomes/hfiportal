from odoo import fields, models


class HrContract(models.Model):
    # In this Odoo build, the Employee Contract model is 'hr.version'
    # (contracts are tracked as versions of the employee record), not the
    # historical standalone 'hr.contract' model.
    _inherit = 'hr.version'

    ph_recurring_allowance_ids = fields.One2many(
        'ph.contract.allowance.line', 'contract_id', string='Recurring PH Allowances',
        help='Taxable/non-taxable allowances that are automatically copied onto every new payslip for this contract.')

    def _get_ph_sss_contribution(self, wage=None):
        """Return the SSS (Regular SS, MPF/WISP, EC) contribution breakdown.
        Called from the PH salary rules with the actual basic salary of the
        payslip period; defaults to the contract wage when not given.
        """
        self.ensure_one()
        wage = self.wage if wage is None else wage
        return self.env['ph.sss.table'].sudo()._get_contribution(wage, company=self.company_id)

    def _get_ph_philhealth_contribution(self, wage=None):
        self.ensure_one()
        wage = self.wage if wage is None else wage
        return self.env['ph.philhealth.config'].sudo()._get_contribution(wage, company=self.company_id)

    def _get_ph_hdmf_contribution(self, wage=None):
        self.ensure_one()
        wage = self.wage if wage is None else wage
        return self.env['ph.hdmf.table'].sudo()._get_contribution(wage, company=self.company_id)
