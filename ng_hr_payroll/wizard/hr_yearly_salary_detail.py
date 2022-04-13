import time

from odoo import models, fields, api, _


class yearly_salary_detail(models.TransientModel):
    _name = "yearly.salary.detail"
    _description = "Hr Salary Employee By Category Report"

    employee_ids = fields.Many2many(
        "hr.employee",
        "payroll_emp_rel",
        "payroll_id",
        "employee_id",
        string="Employees",
        required=True,
    )
    date_from = fields.Date(
        string="Start Date", required=True, default=time.strftime("%Y-01-01")
    )
    date_to = fields.Date(
        string="End Date", required=True, default=time.strftime("%Y-%m-%d")
    )

    def print_report(self, data):
        """
         To get the date and print the report
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: return report
        """
        context = dict(self._context or {})
        active_ids = self.env.context.get("active_ids", [])

        res = self.read()
        res = res and res[0] or {}
        datas = {"ids": active_ids}
        datas.update(
            {"form": res,}
        )

        return self.env["report"].get_action(
            self, "ng_hr_payroll.yearly_salary_ng_report", data=datas
        )
