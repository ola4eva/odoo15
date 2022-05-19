{
    "name": "Internal Requisition",
    "summary": """
    This module allow user to make a request for products from the stock.""",
    "description": """
        Long description of module's purpose
    """,
    "author": "Matt O'Bell",
    "website": "http://www.mattobell.com",
    "category": "Productivity",
    "version": "1.0.0",
    "depends": [
        "base",
        "hr",
        "product",
        "stock",
        "purchase_requisition",
        "ng_navante_base",
        "account_accountant",
        "sale_management",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "data/sequence.xml",
        "views/sale_order.xml",
        "views/ir_request.xml",
        "wizards/ir_request.xml",
    ],
}
