{
    'name': 'Philippine Payroll Extension',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Philippine payroll localization: SSS, PhilHealth, HDMF, loans, allowances and commissions',
    'description': """
Philippine Payroll Extension
=============================
Extends Odoo Payroll (hr_payroll) with Philippine-specific configuration and
computation logic:

* Configurable SSS (Regular SS, MPF/WISP, EC), PhilHealth and HDMF (Pag-IBIG)
  contribution tables (Employee vs. Employer shares).
* Government loan tracking (SSS Loan, HDMF/Pag-IBIG Loan) and internal
  company loans (Emergency Loan, Salary Advance) with balance and payment
  history.
* An "Allowances" tab on the payslip for taxable/non-taxable allowances
  (Rice, Clothing, Laundry, Transportation, ...) that feed into gross pay.
* A manual Commission field on the payslip that feeds into taxable income
  and gross pay.
* Pre-configured salary rule categories, salary rules and a sample
  "Philippines Employee" payroll structure.

IMPORTANT: the seeded SSS / PhilHealth / HDMF figures shipped in this module
are illustrative sample data only. Always verify current rates, brackets and
salary caps against the latest official SSS Circular, PhilHealth Circular and
Pag-IBIG (HDMF) Circular before running live payroll, and update the tables
under PH Payroll Settings accordingly.
""",
    'author': 'HapiHomes',
    'license': 'LGPL-3',
    'depends': ['hr_payroll', 'hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/hr_payslip_input_type_data.xml',
        'data/hr_salary_rule_category_data.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_salary_rule_data.xml',
        'data/ph_loan_type_data.xml',
        'data/ph_allowance_type_data.xml',
        'data/ph_contribution_sample_data.xml',
        'views/ph_sss_table_views.xml',
        'views/ph_philhealth_config_views.xml',
        'views/ph_hdmf_table_views.xml',
        'views/ph_loan_type_views.xml',
        'views/hr_employee_loan_views.xml',
        'views/ph_allowance_type_views.xml',
        'views/ph_overtime_type_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_payslip_views.xml',
        'views/report_payslip_templates.xml',
        'views/ph_payroll_menus.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
