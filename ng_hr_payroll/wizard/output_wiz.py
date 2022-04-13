from odoo import models, fields, api, _


class account_xls_output_wiz(models.TransientModel):
    _name = "account.xls.output.wiz"
    _description = "Wizard to store the Excel output"

    xls_output = fields.Binary(string="Excel Output")
    name = fields.Char(
        string="File Name",
        help="Save report as .xls format",
        default="Payroll_Register.xls",
    )
