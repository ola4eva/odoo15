from odoo import api, fields, models, _


class HrPayslipRun(models.Model):
    _name = "hr.payslip.run"
    _inherit = ["mail.thread.cc", "mail.activity.mixin", "hr.payslip.run"]

    def notify(self, body, subject, users=None, group=None):
        partner_ids = []
        if group:
            users = self.env.ref(group).users.filtered(
                lambda r: r.company_id.id == self.company_id.id
            )
            for user in users:
                partner_ids.append(user.partner_id.id)
        elif users:
            users = self.env["res.users"].browse(users)
            for user in users:
                partner_ids.append(user.partner_id.id)
        if partner_ids:
            self.message_post(
                body=body,
                subject=subject,
                partner_ids=partner_ids,
                message_type="email",
            )
        return True

    state = fields.Selection(selection_add=[("submit", "Submit"), ("close",)])

    def action_submit(self):
        for rec in self:
            body = (
                """<p>This payroll <b>%s</b> has been submitted for approval</p>"""
                % (rec.name,)
            )
            subject = "PAYROLL: %s %s %s" % (rec.name, rec.date_start, rec.date_end)
            rec.notify(body, subject, group="hr.group_hr_manager")
            rec.write({"state": "submit"})
