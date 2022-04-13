from odoo import models, fields, api, _


# class payslip_lines_contribution_register(models.TransientModel):
#     _inherit = "payslip.lines.contribution.register"
#     _description = "PaySlip Lines by Contribution Registers"

#     employee_ids = fields.Many2many("hr.employee", "emp_reg_rel_employee", "employee_id", "wiz_id", string="Employees")

#     def print_report(self):
#         datas = {
#             "ids": self._context.get("active_ids", []),
#             "model": "hr.contribution.register",
#             "form": self.read()[0],
#         }
#         #        return {
#         #            'type': 'ir.actions.report.xml',
#         #            'report_name': 'contribution.register.lines.employee',
#         #            'datas': datas,
#         #        }
#         return self.env["report"].get_action(self, "ng_hr_payroll.contribution_register_mod_report", data=datas)
