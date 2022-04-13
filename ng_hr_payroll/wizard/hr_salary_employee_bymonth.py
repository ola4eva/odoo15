import time

from odoo import models, fields, api, _


class hr_salary_employee_bymonth(models.TransientModel):
    _name = "hr.salary.employee.month"
    _description = "Hr Salary Employee By Month Report"

    @api.model
    def _get_default_category(self):
        category_ids = self.env["hr.salary.rule.category"].search(
            [("code", "=", "NET")]
        )
        return category_ids and category_ids[0] or False

    start_date = fields.Date(
        string="Start Date", required=True, default=time.strftime("%Y-01-01")
    )
    end_date = fields.Date(
        string="End Date", required=True, default=time.strftime("%Y-%m-%d")
    )
    employee_ids = fields.Many2many(
        "hr.employee",
        "payroll_year_rel",
        "payroll_year_id",
        "employee_id",
        string="Employees",
        required=True,
    )
    category_id = fields.Many2one(
        "hr.salary.rule.category",
        string="Category",
        required=True,
        default=_get_default_category,
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
        context = self._context or {}
        datas = {"ids": context.get("active_ids", self._ids)}

        res = self.read()
        res = res and res[0] or {}
        datas.update({"form": res})
        return self.env["report"].get_action(
            self, "ng_hr_payroll.hr_salary_employee_bymonth_ng_report", data=datas
        )
