import time
from datetime import datetime
from dateutil import relativedelta
from odoo.osv import osv

from odoo import models, fields, api, _


class contribution_register_employee(models.TransientModel):
    _name = "contribution.register.employee"
    _description = "Contribution Registers by Employee"

    employee_ids = fields.Many2many(
        "hr.employee",
        "emp_reg_rel",
        "employee_id",
        "wiz_id",
        string="Employees",
        required=True,
    )
    date_from = fields.Date(
        string="Date From", required=True, default=time.strftime("%Y-%m-01")
    )
    date_to = fields.Date(
        string="Date To",
        required=True,
        default=str(
            datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1)
        )[:10],
    )

    def print_report(self):
        datas = {
            "ids": self._context.get("active_ids", []),
            "model": "hr.contribution.register",
            "form": self.read()[0],
        }

        return self.env["report"].get_action(
            self, "ng_hr_payroll.contribution_register_emp_report", data=datas
        )
