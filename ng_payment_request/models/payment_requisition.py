from odoo import fields, models, api, _, exceptions


class AccountMoveInherit(models.Model):
    """docstring for ClassName"""

    _inherit = "account.move.line"

    customer_id = fields.Many2one(comodel_name="res.partner", string="Customer/Vendor")


class PaymentRequestLine(models.Model):
    _name = "payment.requisition.line"
    _description = "payment.requisition.line"

    @api.depends("payment_request_id")
    def check_state(self):
        self.state = self.payment_request_id.state

    name = fields.Char("Description", required=True)
    request_amount = fields.Float("Requested Amount", required=True)
    approved_amount = fields.Float("Approved Amount")
    payment_request_id = fields.Many2one(
        "payment.requisition", string="Payment Request"
    )
    expense_account_id = fields.Many2one("account.account", "Account")
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account"
    )
    state = fields.Char(compute="check_state", string="State")
    partner_id = fields.Many2one("res.partner", string="Customer/Vendor")

    @api.onchange("request_amount")
    def _get_request_amount(self):
        if self.request_amount:
            amount = self.request_amount
            self.approved_amount = amount


class PaymentRequest(models.Model):
    _inherit = ["mail.thread"]
    _name = "payment.requisition"
    _description = "Payment Requisition"

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

    @api.depends(
        "request_line",
        "request_line.request_amount",
        "request_line.approved_amount",
        "state",
    )
    def _compute_requested_amount(self):
        for record in self:
            requested_amount = 0
            approved_amount = 0
            for line in record.request_line:
                requested_amount += line.request_amount
                approved_amount += line.approved_amount
                #
                record.amount_company_currency = approved_amount
                record.approved_amount = approved_amount
                record.requested_amount = requested_amount

            # record.amount_company_currency = requested_amount
            company_currency = record.company_id.currency_id
            current_currency = record.currency_id
            if company_currency != current_currency:
                amount = company_currency.compute(requested_amount, current_currency)
                approved_amount = company_currency.compute(
                    approved_amount, current_currency
                )
                record.amount_company_currency = amount
                record.approved_amount = approved_amount
                record.requested_amount = requested_amount

    name = fields.Char("Name", default="/", copy=False)
    requester_id = fields.Many2one(
        "res.users", "Requester", required=True, default=lambda self: self.env.user
    )
    employee_id = fields.Many2one("hr.employee", "Employee", required=True)
    department_id = fields.Many2one("hr.department", "Department")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    description = fields.Text(string="Description")
    bank_id = fields.Many2one("res.bank", "Bank")
    bank_account = fields.Char("Bank Account", copy=False)
    request_line = fields.One2many(
        "payment.requisition.line", "payment_request_id", string="Lines", copy=False
    )
    requested_amount = fields.Float(
        compute="_compute_requested_amount", string="Requested Amount", store=True
    )
    approved_amount = fields.Float(
        compute="_compute_requested_amount", string="Approved Amount", store=True
    )
    amount_company_currency = fields.Float(
        compute="_compute_requested_amount",
        string="Amount In Company Currency",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "payment.requisition"
        ),
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("line", "Await Line Manager"),
            ("director", "Await Managing Director"),
            ("finance", "Await Finance"),
            ("paid", "Paid"),
            ("refused", "Refused"),
            ("cancelled", "Cancelled"),
        ],
        tracking=True,
        default="draft",
        string="State",
    )

    manager_id = fields.Many2one(
        "res.users", "Manager", readonly=True, related="employee_id.parent_id.user_id"
    )

    need_gm_approval = fields.Boolean(
        "Needs First Approval?", copy=False, readonly=True
    )
    need_md_approval = fields.Boolean(
        "Needs Final Approval?", copy=False, readonly=True
    )
    manging_director_id = fields.Many2one(
        "hr.employee", "Managing Director", readonly=True
    )
    dept_manager_id = fields.Many2one(
        "hr.employee", "Department Manager", readonly=True
    )
    dept_manager_approve_date = fields.Date(
        "Approved By Department Manager On", readonly=True
    )
    gm_approve_date = fields.Date("First Approved On", readonly=True)
    director_approve_date = fields.Date("Final Approved On", readonly=True)
    move_id = fields.Many2one("account.move", string="Journal Entry")
    journal_id = fields.Many2one("account.journal", string="Journal")
    update_cash = fields.Boolean(
        string="Update Cash Register?",
        readonly=False,
        states={"draft": [("readonly", True)]},
        help="Tick if you want to update cash register by creating cash transaction line.",
    )
    cash_id = fields.Many2one(
        "account.bank.statement",
        string="Cash Register",
        domain=[("journal_id.type", "in", ["cash"]), ("state", "=", "open")],
        required=False,
        readonly=False,
        states={"draft": [("readonly", False)]},
    )

    @api.model
    def create(self, vals):
        if not vals.get("name"):
            vals["name"] = self.env["ir.sequence"].get("payment.requisition")
        return super(PaymentRequest, self).create(vals)

    @api.onchange("requester_id")
    def onchange_requester(self):
        employee = self.env["hr.employee"].search(
            [("user_id", "=", self._uid)], limit=1
        )
        self.employee_id = employee.id
        self.department_id = (
            employee.department_id and employee.department_id.id or False
        )

    def action_confirm(self):
        if not self.request_line:
            raise exceptions.Warning(
                _("Can not confirm request without request lines.")
            )
        body = _(
            "<p>Payment Requisition request %s has been submitted by <b>%s</b>.</p> <p>Please kindly chec.</p>"
            % (self.name, self.env.user.partner_id.name)
        )
        subject = _("Payment Requisition %s" % (self.name,))
        self.notify(body, subject, users=self.employee_id.parent_id.user_id.ids)
        return self.write({"state": "line"})

    def action_line_approve(self):
        body = _(
            "<p>Payment Requisition request %s has been confirmed by <b>%s</b>.</p> <p>Please kindly check and approve.</p>"
            % (self.name, self.env.user.partner_id.name)
        )
        subject = _("Payment Requisition %s" % (self.name,))
        self.notify(
            body, subject, group="ng_internal_requisition.group_managing_director"
        )
        return self.write({"state": "director"})

    def action_director_approve(self):
        body = _(
            "<p>Payment Requisition request %s has been confirmed by <b>%s</b>.</p> <p>Please check and approve.</p>"
            % (self.name, self.env.user.partner_id.name)
        )
        subject = _("Payment Requisition %s" % (self.name,))

        self.notify(body, subject, group="account.group_account_manager")
        return self.write({"state": "finance"})

    def action_pay(self):
        move_obj = self.env["account.move"]
        move_line_obj = self.env["account.move.line"]
        currency_obj = self.env["res.currency"]
        statement_line_obj = self.env["account.bank.statement.line"]

        ctx = dict(self._context or {})
        for record in self:
            company_currency = record.company_id.currency_id
            current_currency = record.currency_id

            ctx.update({"date": record.date})

            amount = current_currency.compute(record.approved_amount, company_currency)
            if record.journal_id.type == "purchase":
                sign = 1
            else:
                sign = -1
            asset_name = record.name
            reference = record.name

            move_vals = {
                "date": record.date,
                "ref": reference,
                "journal_id": record.journal_id.id,
            }

            move_id = move_obj.with_context(check_move_validity=False).create(move_vals)
            journal_id = record.journal_id.id
            partner_id = record.employee_id.address_home_id
            if not partner_id:
                raise exceptions.Warning(
                    _("Please specify Employee Home Address in the Employee Form!.")
                )
            for line in record.request_line:
                amount_line = current_currency.compute(
                    line.approved_amount, company_currency
                )
                move_line_obj.with_context(check_move_validity=False).create(
                    {
                        "name": asset_name,
                        "ref": reference,
                        "move_id": move_id.id,
                        "account_id": line.expense_account_id.id,
                        "credit": 0.0,
                        "debit": amount_line,
                        "journal_id": journal_id,
                        "partner_id": partner_id.id,
                        "customer_id": line.partner_id.id,
                        "currency_id": company_currency.id != current_currency.id
                        and current_currency.id
                        or False,
                        "amount_currency": company_currency.id != current_currency.id
                        and sign * line.approved_amount
                        or 0.0,
                        "analytic_account_id": line.analytic_account_id
                        and line.analytic_account_id.id
                        or False,  # 26 Aug 2016
                        "date": record.date,
                    }
                )
            move_line_obj.with_context(check_move_validity=False).create(
                {
                    "name": asset_name,
                    "ref": reference,
                    "move_id": move_id.id,
                    "account_id": record.journal_id.default_account_id.id,
                    "debit": 0.0,
                    "credit": amount,
                    "journal_id": journal_id,
                    "partner_id": partner_id.id,
                    "customer_id": line.partner_id.id,
                    "currency_id": company_currency.id != current_currency.id
                    and current_currency.id
                    or False,
                    "amount_currency": company_currency.id != current_currency.id
                    and sign * record.approved_amount
                    or 0.0,
                    "date": record.date,
                }
            )
            record.move_id = move_id.id
            if record.update_cash:
                type = "general"
                amount = -1 * record.approved_amount
                account = record.journal_id.default_debit_account_id.id
                if not record.journal_id.type == "cash":
                    raise exceptions.Warning(
                        _("Journal should match with selected cash register journal.")
                    )
                stline_vals = {
                    "name": record.name or "?",
                    "amount": amount,
                    "type": type,
                    "account_id": account,
                    "statement_id": record.cash_id.id,
                    "ref": record.name,
                    "partner_id": partner_id.id,
                    "date": record.date,
                    "PaymentRequest_id": record.id,
                }
                statement_line_obj.create(stline_vals)
        self.state = "paid"
        return True

    def action_cancel(self):
        self.state = "cancelled"
        return True

    def action_reset(self):
        self.state = "draft"
        return True

    def action_refuse(self):
        self.state = "refused"
        return True


class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    PaymentRequest_id = fields.Many2one("payment.requisition", string="Payment Request")
