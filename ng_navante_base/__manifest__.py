{
    "name": "Navante Base",
    "summary": """Navante Base""",
    "description": """Navante Base""",
    "author": "My Company",
    "website": "http://www.yourcompany.com",
    "category": "Uncategorized",
    "version": "1.0",
    "depends": [
        "base",
        "purchase",
        "stock_account",
        "hr_payroll",
        "hr_payroll_account",
        "hr_contract_salary",
    ],
    "data": [
        # 'security/ir.model.access.csv',
        "views/views.xml",
        "views/purchase_order.xml",
        "data/ir_sequence.xml",
    ],
}
