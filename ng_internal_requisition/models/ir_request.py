from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from urllib.parse import urljoin, urlencode

STATES = [
    ("draft", "Draft"),
    ("parent", "Await Line Manager"),
    ("procurement", "Await Procurement"),
    ("await", "Await Another Operation"),
    ("project", "Await Project Manager"),
    ("md", "Await M.D"),
    ("done", "Done"),
]


class IRRequest(models.Model):

    _name = "ng.ir.request"
    _inherit = ["mail.thread"]
    _description = "Internal Requisition"
    _order = "create_date desc"

    def notify(self, body, subject, users=None, group=None):
        partner_ids = []
        if group:
            users = self.env.ref(group).users
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

    def _current_login_user(self):
        """Return current logined in user."""
        return self.env.user.id

    def _current_login_employee(self):
        """Get the employee record related to the current login user."""
        hr_employee = self.env["hr.employee"].search(
            [("user_id", "=", self._current_login_user())], limit=1
        )
        return hr_employee.id

    name = fields.Char(string="Name", default="/", required=True)
    state = fields.Selection(selection=STATES, default="draft", tracking=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        default=_current_login_user,
        tracking=True,
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        default=_current_login_employee,
        required=True,
    )
    request_date = fields.Date(
        string="Date",
        default=lambda self: fields.Date.today(),
        help="The day which te request was made",
    )
    date_deadline = fields.Date(string="Deadline")
    manager_id = fields.Many2one(
        comodel_name="hr.employee", related="employee_id.parent_id", string="Manager"
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        related="employee_id.department_id",
        string="Department",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env["res.company"]._company_default_get(),
        index=True,
        required=True,
    )

    order_count = fields.Integer(string="Order Count", compute="_compute_order_count")
    requisition_count = fields.Integer(
        string="Order Count", compute="_compute_requisition_count"
    )
    agrement_id = fields.Many2one(comodel_name="purchase.requisition")
    purchase_id = fields.Many2one(
        comodel_name="purchase.order", string="Purchase Order", copy=False
    )

    line_ids = fields.One2many(
        comodel_name="ng.ir.request.line",
        inverse_name="request_id",
        string="Request Line",
        required=True,
        copy=True,
    )
    reason = fields.Text(string="Rejection Reason")
    is_manager = fields.Boolean(compute="_compute_is_manager")

    @api.depends("agrement_id")
    def _compute_requisition_count(self):
        for rec in self:
            rec.requisition_count = len(rec.agrement_id.ids)

    @api.depends("agrement_id")
    def _compute_order_count(self):
        for rec in self:
            rec.order_count = len(rec.agrement_id.purchase_ids)

    @api.depends("manager_id", "employee_id")
    def _compute_is_manager(self):
        for rec in self:
            rec.is_manager = self.env.user.id == rec.manager_id.user_id.id

    @api.model
    def create(self, vals):
        seq = self.env["ir.sequence"].next_by_code("ng.ir.request")
        vals.update(name=seq)
        res = super(IRRequest, self).create(vals)
        return res

    def submit(self):
        if not self.line_ids:
            raise UserError("You can not submit an empty item list for requisition.")
        else:
            body = """<p>Hi %s</p>
                <p>%s Submitted %s for your approval.</p>
                <br/>
                <p>Thanks</p>
            """ % (
                self.manager_id.user_id.name,
                self.env.user.name,
                self.name,
            )
            subject = "Requisition Approval %s" % (self.name,)
            self.notify(body, subject, users=self.manager_id.user_id.ids)
            self.write({"state": "parent"})

    def line_manager_approve(self):
        context = self.env.context
        if self:
            approved = context.get("approved")
            if not approved:
                # send rejection mail to the author.
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "ir.request.wizard",
                    "views": [[False, "form"]],
                    "context": {"request_id": self.id},
                    "target": "new",
                }
            else:
                body = """<p>Hi!</p>
                <p>%s Forwarded %s requisition for your approval.</p>
                <br/>
                <p>Thanks</p>
            """ % (
                    self.env.user.name,
                    self.name,
                )
            subject = "Requisition Approval %s" % (self.name,)
            self.notify(body, subject, group="purchase.group_purchase_user")
            self.write({"state": "procurement"})

    def procurement_approve(self):
        context = self.env.context
        approved = context.get("approved")
        if not approved:
            # send mail to the author.
            return {
                "type": "ir.actions.act_window",
                "res_model": "ir.request.wizard",
                "views": [[False, "form"]],
                "context": {"request_id": self.id},
                "target": "new",
            }
        else:
            payload = {
                "origin": self.name,
                "ordering_date": fields.Date.today(),
                "date_end": self.date_deadline,
                "requisition_id": self.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": line.product_id.id,
                            "product_qty": line.quantity,
                            "qty_ordered": line.quantity,
                            "product_uom_id": line.uom_id.id,
                        },
                    )
                    for line in self.line_ids
                ],
            }
            rec = self.env["purchase.requisition"].create(payload)
            action = {
                "type": "ir.actions.act_window",
                "res_model": "purchase.requisition",
                "views": [[False, "form"]],
                "res_id": rec.id,
                "target": "self",
            }
            rec.action_in_progress()
            self.write({"state": "await", "agrement_id": rec.id})
            return action

    def procurement_approve_done(self, agrement_id):
        body = """<p>Hi!</p>
                <p>%s Forwarded %s requisition for your review and approval.</p>
                <br/>
                <p>Thanks</p>
            """ % (
            self.env.user.name,
            self.name,
        )
        subject = "Requisition Approval %s" % (self.name,)
        self.notify(
            body, subject, group="ng_internal_requisition.group_project_manager"
        )
        self.write({"state": "project"})

    def action_open_purchase_requisition_list(self):
        """."""
        action = {
            "name": self.agrement_id.name,
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [("id", "in", self.agrement_id.purchase_ids.ids)],
            "target": "self",
        }
        return action

    def action_show_requisition_count(self):
        action = {
            "name": self.agrement_id.name,
            "type": "ir.actions.act_window",
            "res_model": "purchase.requisition",
            "views": [[False, "form"]],
            "res_id": self.agrement_id.id,
            "target": "self",
        }
        return action

    def project_manager_approve(self):
        for rec in self:
            context = self.env.context
            approved = context.get("approved")
            if not approved:
                pass
            else:
                body = """<p>Hi!</p>
                <p>%s Forwarded %s requisition for your review and approval.</p>
                <br/>
                <p>Thanks</p>
            """ % (
                    self.env.user.name,
                    self.name,
                )
        subject = "Requisition Approval %s" % (self.name,)
        self.notify(
            body, subject, group="ng_internal_requisition.group_managing_director"
        )
        self.purchase_id.button_confirm()
        self.write({"state": "md"})

    def manager_approve(self):
        body = """<p>Hi!</p>
                <p>This requisition %s has been approved by  %s.</p>
                 <p>Kindly made available the total sum of %s to payoff the vendor.</p>
                <br/>
                <p>Thanks</p>
            """ % (
            self.name,
            self.env.user.name,
            self.purchase_id.amount_total,
        )
        subject = "Requisition Approval %s" % (self.name,)
        self.notify(body, subject, group="account.group_account_manager")
        self.write({"state": "done"})

    def action_reject(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "ir.request.wizard",
            "views": [[False, "form"]],
            "context": {"request_id": self.id},
            "target": "new",
        }
