from odoo import models, fields, api, _


class Company(models.Model):
    _inherit = "res.company"
    _description = "Company"

    thirteen_salary = fields.Boolean(
        string="13 Month Salary",
        help="Tick if your company provide thirteen month salary to employees",
    )
    union_policy = fields.Many2many(
        "union.policy",
        "company_policy_rel",
        "company_id",
        "union_id",
        string="Union Policies",
    )
    notice_period = fields.Float(string="Notice Period by Employee", help="In Months")
    terminal_policy = fields.Many2one("terminal.policy", string="Terminal Policy")
    company_notice_period = fields.Float(
        string="Notice Period by Employer", help="In Months"
    )
    no_payroll_run = fields.Integer(
        string="Total Number of Payroll",
        default=1,
        help="Please specify total number of payroll company can run in month for single employee or batch of employee",
    )
