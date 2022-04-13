import time
import datetime
from odoo import api, fields, models

mnths = []
mnths_total = []
rules = []
rules_data = []
total = 0.0


class payroll_register_report(models.AbstractModel):
    _name = "report.ng_hr_payroll.payroll_register_report"

    def get_periods(self, form):

        mnth_name = []
        # rules = []
        #        category_id = form.get('category_id', [])
        #        category_id = category_id and category_id[0] or False
        #        rule_ids = self.pool.get('hr.salary.rule').search(self.cr, self.uid, [('category_id', '=', category_id)])
        rule_ids = form.get("rule_ids", [])

        if rule_ids:
            for r in self.env["hr.salary.rule"].browse(rule_ids):
                mnth_name.append(r.name)
                global rules
                rules.append(r.id)
        # global rules
        # global rules_data
        rules = rules
        rules_data = mnth_name
        return [mnth_name]

    def get_salary(self, form, emp_id, emp_salary, total_mnths):

        total = 0.0
        cnt = 0
        flag = 0
        #        for r in self.rules:
        for r in self.env["hr.salary.rule"].browse(self.rules):
            self._cr.execute(
                "select pl.name as name ,pl.total \
                                 from hr_payslip_line as pl \
                                 left join hr_payslip as p on pl.slip_id = p.id \
                                 left join hr_employee as emp on emp.id = p.employee_id \
                                 left join resource_resource as r on r.id = emp.resource_id  \
                                where p.employee_id = %s and pl.salary_rule_id = %s \
                                and (p.date_from >= %s) AND (p.date_to <= %s) \
                                group by pl.total,r.name, pl.name,emp.id",
                (
                    emp_id,
                    r.id,
                    form.get("start_date", False),
                    form.get("end_date", False),
                ),
            )
            sal = self._cr.fetchall()
            salary = dict(sal)
            cnt += 1
            flag += 1
            if flag > 8:
                continue
            if r.name in salary:
                emp_salary.append(salary[r.name])
                total += salary[r.name]
                total_mnths[cnt] = total_mnths[cnt] + salary[r.name]
            else:
                emp_salary.append("")

        if len(self.rules) < 8:
            diff = 8 - len(self.rules)
            for x in range(0, diff):
                emp_salary.append("")
        return emp_salary, total, total_mnths

    def get_salary1(self, form, emp_id, emp_salary, total_mnths):

        total = 0.0
        cnt = 0
        flag = 0
        for r in self.env["hr.salary.rule"].browse(rules or []):
            self._cr.execute(
                "select pl.name as name ,pl.total \
                                 from hr_payslip_line as pl \
                                 left join hr_payslip as p on pl.slip_id = p.id \
                                 left join hr_employee as emp on emp.id = p.employee_id \
                                 left join resource_resource as r on r.id = emp.resource_id  \
                                where p.employee_id = %s and pl.salary_rule_id = %s \
                                and (p.date_from >= %s) AND (p.date_to <= %s) \
                                group by pl.total,r.name, pl.name,emp.id",
                (
                    emp_id,
                    r.id,
                    form.get("start_date", False),
                    form.get("end_date", False),
                ),
            )

            sal = self._cr.fetchall()
            salary = dict(sal)
            cnt += 1
            flag += 1

            if r.name in salary:
                emp_salary.append(salary[r.name])
                total += salary[r.name]
                total_mnths[cnt] = total_mnths[cnt] + salary[r.name]
            else:
                emp_salary.append("")

        return emp_salary, total, total_mnths

    def get_employee(self, form, excel=False):
        emp_salary = []
        salary_list = []
        total_mnths = [
            "Total",
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]  # only for pdf report!
        emp_obj = self.env["hr.employee"]
        emp_ids = form.get("employee_ids", [])

        total_excel_months = [
            "Total",
        ]  # for excel report
        for r in range(0, len(rules)):
            total_excel_months.append(0)
        employees = emp_obj.browse(emp_ids)
        for emp_id in employees:
            emp_salary.append(emp_id.name)
            total = 0.0
            if excel:
                emp_salary, total, total_mnths = self.get_salary1(
                    form, emp_id.id, emp_salary, total_mnths=total_excel_months
                )
            else:
                emp_salary, total, total_mnths = self.get_salary(
                    form, emp_id.id, emp_salary, total_mnths
                )
            emp_salary.append(total)
            salary_list.append(emp_salary)
            emp_salary = []
        mnths_total.append(total_mnths)
        return salary_list

    def get_months_tol(self):
        global mnths_total
        return mnths_total

    def get_total(self):
        for item in self.mnths_total:
            for count in range(1, len(item)):
                if item[count] == "":
                    continue
                self.total += item[count]
        return self.total

    @api.model
    def render_html(self, docids, data=None):
        docs = self.env["hr.employee"].browse(data["form"]["employee_ids"])
        docargs = {
            "time": time,
            "get_employee": self.get_employee,
            "get_periods": self.get_periods,
            "get_months_tol": self.get_months_tol,
            "get_total": self.get_total,
            "doc_ids": data["form"]["employee_ids"],
            "doc_model": "hr.employee",
            "docs": docs,
            "data": data,
            "company": self.env.user.company_id,
        }
        return self.env["report"].render(
            "ng_hr_payroll.payroll_register_report", values=docargs
        )
