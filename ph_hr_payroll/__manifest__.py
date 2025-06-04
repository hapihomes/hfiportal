{
    # Module metadata
    'name': 'Philippines HR Payroll Localization',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'PH Attendance, Leave, Loan, and Government Deductions for Payslips',
    'depends': ['hr', 'hr_payroll', 'hr_holidays'],  # Dependencies required
    'data': [
        'data/hr_structure.xml',
        'data/hr_salary_rules.xml',
        'views/hr_loan_views.xml',
        'views/hr_government_views.xml',
    ],
    'installable': True,
}
