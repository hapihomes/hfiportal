{
    "name": "Employee Loan",
    "version": "1.0",
    "category": "Human Resources",
    "summary": "Manage employee loans",
    "depends": ["base", "hr"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_loan_views.xml",
        "views/hr_loan_menu.xml"
    ],
    "installable": True,
    "application": True
}