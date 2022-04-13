import time
from datetime import datetime

from odoo import api, fields, models

total_bysal = 0


class report_payroll_advice(models.AbstractModel):
    _name = "report.ng_hr_payroll.ng_payroll_advise_report"

    def get_month(self, input_date):
        payslip_pool = self.env["hr.payslip"]
        res = {"from_name": "", "to_name": ""}
        slip_ids = payslip_pool.search(
            [("date_from", "<=", input_date), ("date_to", ">=", input_date)]
        )
        if slip_ids:
            slip = payslip_pool.browse(slip_ids)[0]
            from_date = datetime.strptime(slip.date_from, "%Y-%m-%d")
            to_date = datetime.strptime(slip.date_to, "%Y-%m-%d")
            res["from_name"] = (
                from_date.strftime("%d")
                + "-"
                + from_date.strftime("%B")
                + "-"
                + from_date.strftime("%Y")
            )
            res["to_name"] = (
                to_date.strftime("%d")
                + "-"
                + to_date.strftime("%B")
                + "-"
                + to_date.strftime("%Y")
            )
        return res

    def get_bysal_total(self):
        return total_bysal

    def get_detail(self, line_ids):
        result = []
        global total_bysal

        total_bysal = 0.00
        count = 0
        for l in line_ids:
            res = {}
            count = count + 1
            res.update(
                {
                    "name": l.employee_id.name,
                    "count": count,
                    "acc_no": l.name,
                    "ifsc_code": l.ifsc_code,
                    "bank_name": l.bank_name,
                    "bysal": l.bysal,
                    "debit_credit": l.debit_credit,
                }
            )
            total_bysal += l.bysal
            result.append(res)
        return result

    @api.model
    def render_html(self, docids, data=None):
        docs = self.env["hr.payroll.advice"].browse(docids)
        docargs = {
            "time": time,
            "get_month": self.get_month,
            # 'convert': self.convert,
            "get_detail": self.get_detail,
            "get_bysal_total": self.get_bysal_total,
            "doc_ids": docids,
            "doc_model": "hr.payroll.advice",
            "docs": docs,
            "company": self.env.user.company_id,
        }
        return self.env["report"].render(
            "ng_hr_payroll.ng_payroll_advise_report", values=docargs
        )

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["hr.payroll.advice"].browse(docids)
        return {
            "time": time,
            "get_month": self.get_month,
            "get_detail": self.get_detail,
            "get_bysal_total": self.get_bysal_total,
            "doc_ids": docids,
            "doc_model": "hr.payroll.advice",
            "docs": docs,
            "company": self.env.user.company_id,
        }
