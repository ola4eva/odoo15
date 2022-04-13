from odoo import fields, api, _, models


class hr_payslip_run(models.Model):
    _inherit = "hr.payslip.run"
    _description = "Payslip Batches"

    def cancel_batch(self):
        return self.write({"state": "cancel"})

    mid_month = fields.Boolean(
        string="Mid Month Payroll",
        help="Tick if you want to process for mid month payroll.",
    )
    mid_percentage = fields.Float(
        string="Percentage",
        help="Enter the percentage of selected structure to process: 0-100",
    )
    old_percentage = fields.Float(
        string="Last Percentage",
        help="% for previous mid month payroll 0-100 processed. Here you have to specify the percentage of mid month payroll which you processed previously.",
    )
    available_advice = fields.Boolean(
        string="Made Payment Advice?",
        help="If this box is checked which means that Payment Advice exists for current batch",
    )

    pay_type = fields.Selection(
        selection=[("fix", "Fix Percentage"), ("dynamic", "Dynamic")],
        string="Payslip Type",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default="dynamic",
    )
    struct_id = fields.Many2one(
        "hr.payroll.structure",
        string="Structure",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Keep Empty if you want to use structure define on contract of employee.",
    )
    journal_id = fields.Many2one("account.journal", related="struct_id.journal_id")

    def copy(self, default={}):
        if not default:
            default = {}
        default.update({"available_advice": False})
        return super(hr_payslip_run, self).copy(default)

    def close_payslip_run(self):
        """close_payslip_run."""

        res = super(hr_payslip_run, self).close_payslip_run()
        for slip_id in self.slip_ids:
            slip_id.action_payslip_done()
        return res

    def close_payslip_run_dummy(
        self,
    ):  # can be removed.#TypeError: 'NoneType' object is not callable
        res = super(hr_payslip_run, self).close_payslip_run()
        for b in self:
            for p in b.slip_ids:
                p.compute_sheet()  # TypeError: 'NoneType' object is not callable
                p.signal_workflow("hr_verify_sheet")
        return res

    def draft_payslip_run(self):
        res = super(hr_payslip_run, self).draft_payslip_run()
        self.write({"available_advice": False})
        return res

    def create_advice(self):
        res = super(hr_payslip_run, self).create_advice()
        payslip_line_pool = self.env["hr.payslip.line"]
        advice_pool = self.env["hr.payroll.advice"]
        advice_line_pool = self.env["hr.payroll.advice.line"]
        for run in self:
            if run.available_advice:
                raise Warning(
                    _(
                        "Payment advice already exists for %s, 'Set to Draft' to create a new advice."
                    )
                    % (run.name)
                )
            advice_data = {
                "batch_id": run.id,
                "company_id": self.env.user.company_id.id,
                "name": run.name,
                "date": run.date_end,
                "bank_id": self.env.user.company_id.partner_id.bank_ids
                and self.env.user.company_id.partner_id.bank_ids[0].bank_id
                and self.env.user.company_id.partner_id.bank_ids[0].bank_id.id
                or False,
            }
            advice_id = advice_pool.create(advice_data)
            slip_ids = []
            for slip_id in run.slip_ids:
                slip_ids.append(slip_id)

            for slip in slip_ids:
                if (
                    not slip.employee_id.bank_account_id
                    or not slip.employee_id.bank_account_id.acc_number
                ):
                    raise Warning(
                        _("Please define bank account for the %s employee")
                        % (slip.employee_id.name)
                    )
                line_ids = payslip_line_pool.search(
                    [("slip_id", "=", slip.id), ("code", "=", "NET")], limit=1
                )
                if line_ids:
                    advice_line = {
                        "advice_id": advice_id.id,
                        "name": slip.employee_id.bank_account_id.acc_number,
                        "employee_id": slip.employee_id.id,
                        "ifsc_code": slip.employee_id.bank_account_id.bank_id.bic,
                        "bysal": line_ids.total,
                    }
                    advice_line_pool.create(advice_line)
        self.write({"available_advice": True})
        return res

    def draft_payslip_run(self):
        res = super(hr_payslip_run, self).draft_payslip_run()
        self.write({"available_advice": False})
        return res

    def create_advice(self):
        payslip_line_pool = self.env["hr.payslip.line"]
        advice_pool = self.env["hr.payroll.advice"]
        advice_line_pool = self.env["hr.payroll.advice.line"]
        for run in self:
            if run.available_advice:
                raise Warning(
                    _(
                        "Payment advice already exists for %s, 'Set to Draft' to create a new advice."
                    )
                    % (run.name)
                )
            advice_data = {
                "batch_id": run.id,
                "company_id": self.env.user.company_id.id,
                "name": run.name,
                "date": run.date_end,
                "bank_id": self.env.user.company_id.partner_id.bank_ids
                and self.env.user.company_id.partner_id.bank_ids[0].bank_id
                and self.env.user.company_id.partner_id.bank_ids[0].bank_id.id
                or False,
            }
            advice_id = advice_pool.create(advice_data)
            slip_ids = []
            for slip_id in run.slip_ids:
                slip_ids.append(slip_id)

            for slip in slip_ids:
                if (
                    not slip.employee_id.bank_account_id
                    or not slip.employee_id.bank_account_id.acc_number
                ):
                    raise Warning(
                        _("Please define bank account for the %s employee")
                        % (slip.employee_id.name)
                    )
                line_ids = payslip_line_pool.search(
                    [("slip_id", "=", slip.id), ("code", "=", "NET")], limit=1
                )
                if line_ids:
                    advice_line = {
                        "advice_id": advice_id.id,
                        "name": slip.employee_id.bank_account_id.acc_number,
                        "employee_id": slip.employee_id.id,
                        "ifsc_code": slip.employee_id.bank_account_id.bank_id.bic,
                        "bysal": line_ids.total,
                    }
                    advice_line_pool.create(advice_line)
        return self.write({"available_advice": True})


class hr_payslip_ot(models.Model):
    """
    Payslip Overtime
    """

    _name = "hr.payslip.ot"
    _description = "Payslip Overtime"

    name = fields.Char(string="Description", required=True)
    number_of_days = fields.Float(string="Number of Days")
    number_of_hours = fields.Float(string="Number of Hours")
    payslip_id = fields.Many2one(
        "hr.payslip", string="Pay Slip", required=True, ondelete="cascade", index=True
    )


class hr_payslip(models.Model):
    """
    Employee Pay Slip
    """

    _inherit = "hr.payslip"
    _description = "Pay Slips"

    ot_ids = fields.One2many(
        "hr.payslip.ot",
        "payslip_id",
        string="Overtime",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    advice_id = fields.Many2one(
        "hr.payroll.advice",
        string="Bank Advice",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    mid_month = fields.Boolean(
        string="Mid Month Payroll",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Tick if you want to process for mid month payroll",
    )
    mid_percentage = fields.Float(
        string="Percentage",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Enter the percentage of selected structure to process: 0-100",
    )
    old_percentage = fields.Float(
        string="Last Percentage",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="% for previous mid month payroll 0-100 processed. Here you have to specify the percentage of mid month payroll which you processed previously. Keep 0 for normal payroll.",
    )

    pay_type = fields.Selection(
        selection=[("fix", "Fix Percentage"), ("dynamic", "Dynamic")],
        string="Payslip Type",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default="dynamic",
    )

    def onchange_employee_id(
        self, date_from, date_to, employee_id=False, contract_id=False
    ):
        ot_obj = self.env["hr.payslip.ot"]
        res = super(hr_payslip, self).onchange_employee_id(
            date_from, date_to, employee_id, contract_id
        )
        # delete old ot days lines
        old_ot_days_ids = (
            self.ids and ot_obj.search([("payslip_id", "=", self.ids[0])]) or False
        )
        if old_ot_days_ids:
            old_ot_days_ids.unlink()
        if (not employee_id) or (not date_from) or (not date_to):
            return res

        obj = self.env["hr.overtime"]
        ot_list = []
        ot_ids = obj.search(
            [
                ("employee_id", "=", employee_id),
                ("state", "=", "validate"),
                ("include_payroll", "=", True),
                ("date_from", ">=", date_from),
                ("date_to", "<=", date_to),
            ]
        )
        for ot in ot_ids:
            ot_list.append(
                {
                    "name": ot.name,
                    "number_of_hours": ot.number_of_hours,
                    "number_of_days": ot.number_of_days,
                }
            )
        if ot_list:
            res["value"].update({"ot_ids": ot_list})
        return res

    # For mid month Payroll we override get_payslip_lines
    @api.model
    def get_payslip_lines(self, contract_ids, payslip_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(
                    localdict, category.parent_id, amount
                )
            localdict["categories"].dict[category.code] = (
                category.code in localdict["categories"].dict
                and localdict["categories"].dict[category.code] + amount
                or amount
            )
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict):
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code),
                )
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """
                    SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code),
                )
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """Class that will be used into the python code, mainly for usability purposes."""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                    (self.employee_id, from_date, to_date, code),
                )
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

            def get_installement(self, emp_id, date_from, date_to=None):
                if date_to is None:
                    date_to = datetime.now().strftime("%Y-%m-%d")
                self._cr.execute(
                    "SELECT sum(total) from loan_installment_details as i, loan_type as t, employee_loan_details as l where \
                                    i.employee_id=%s  \
                                    and t.id = i.loan_type and t.payment_method='salary' and \
                                    i.loan_id = l.id and l.state='disburse' AND i.state != 'paid' AND i.date_to >= %s AND i.date_to <= %s ",
                    (self.employee_id, date_from, date_to),
                )

                res = self._cr.fetchone()
                return res and res[0] or 0.0

            def get_overtime_days(
                self, emp_id, date_from, date_to=None
            ):  # not working for 30th date..it skip it..need to fix
                if date_to is None:
                    date_to = fields.Date.today()
                self._cr.execute(
                    "SELECT sum(o.number_of_days) from hr_overtime as o where \
                                    o.include_payroll IS TRUE and o.employee_id=%s \
                                    and o.state='validate' AND to_char(o.date_to, 'YYYY-MM-DD') >= %s AND to_char(o.date_to, 'YYYY-MM-DD') <= %s ",
                    (self.employee_id, date_from, date_to),
                )
                res = self._cr.fetchone()
                return res and res[0] or 0.0

            def get_overtime_hours(self, emp_id, date_from, date_to=None):
                if date_to is None:
                    date_to = fields.Date.today()
                self._cr.execute(
                    "SELECT sum(o.number_of_hours) from hr_overtime as o where \
                                    o.include_payroll IS TRUE and o.employee_id=%s \
                                    and o.state='validate' AND to_char(o.date_to, 'YYYY-MM-DD') >= %s AND to_char(o.date_to, 'YYYY-MM-DD') <= %s ",
                    (self.employee_id, date_from, date_to),
                )
                res = self._cr.fetchone()
                return res and res[0] or 0.0

            def get_expert_days(
                self, emp_id, date_from, date_to=None
            ):  # not working for 30th date..it skip it..need to fix
                if date_to is None:  # manpower module
                    date_to = fields.Date.today()
                self._cr.execute(
                    "SELECT sum(o.number_of_days) from expert_workdays as o where \
                                    o.include_payroll IS TRUE and o.employee_id=%s \
                                    and o.state='validate' AND to_char(o.date_to, 'YYYY-MM-DD') >= %s AND to_char(o.date_to, 'YYYY-MM-DD') <= %s ",
                    (self.employee_id, date_from, date_to),
                )
                res = self._cr.fetchone()
                return res and res[0] or 0.0

            def get_expert_hours(self, emp_id, date_from, date_to=None):
                if date_to is None:  # manpower module
                    date_to = fields.Date.today()
                self._cr.execute(
                    "SELECT sum(o.number_of_hours) from expert_workdays as o where \
                                    o.include_payroll IS TRUE and o.employee_id=%s \
                                    and o.state='validate' AND to_char(o.date_to, 'YYYY-MM-DD') >= %s AND to_char(o.date_to, 'YYYY-MM-DD') <= %s ",
                    (self.employee_id, date_from, date_to),
                )
                res = self._cr.fetchone()
                return res and res[0] or 0.0

            def get_timesheet_lines(
                self, emp_id, date_from, date_to=None, anlaytic_account=False
            ):
                if date_to is None:
                    date_to = fields.Date.today()
                if anlaytic_account:  # expert anlaytic account timesheet bdu.
                    self._cr.execute(
                        "SELECT sum(a.unit_amount) from hr_timesheet_sheet_sheet as h, hr_analytic_timesheet as o, account_analytic_line as a where \
                                        o.sheet_id=h.id and h.employee_id=%s and a.id=o.line_id \
                                        and h.state='done' AND to_char(a.date, 'YYYY-MM-DD') >= %s AND to_char(a.date, 'YYYY-MM-DD') <= %s and a.account_id=%s ",
                        (self.employee_id, date_from, date_to, anlaytic_account),
                    )
                else:
                    self._cr.execute(
                        "SELECT sum(a.unit_amount) from hr_timesheet_sheet_sheet as h, hr_analytic_timesheet as o, account_analytic_line as a where \
                                        o.sheet_id=h.id and h.employee_id=%s and a.id=o.line_id \
                                        and h.state='done' AND to_char(a.date, 'YYYY-MM-DD') >= %s AND to_char(a.date, 'YYYY-MM-DD') <= %s",
                        (self.employee_id, date_from, date_to),
                    )
                res = self._cr.fetchone()
                return res and res[0] or 0.0

        # New ---------------------------
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env["hr.payslip"].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {})
        inputs = InputLine(payslip.employee_id.id, inputs_dict)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict)
        payslips = Payslips(payslip.employee_id.id, payslip)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict)

        baselocaldict = {
            "categories": categories,
            "rules": rules,
            "payslip": payslips,
            "worked_days": worked_days,
            "inputs": inputs,
        }
        # get the ids of the structures on the contracts and their parent id as well
        contracts = self.env["hr.contract"].browse(contract_ids)
        if payslip.struct_id:  # probuse
            structure_ids = [payslip.struct_id.id]  # probuse
            #             structure_ids.extend(self.env['hr.payroll.structure']._get_parent_structure(structure_ids))
            structure_ids.extend(
                payslip.struct_id._get_parent_structure().ids
            )  # probuse
        else:  # probuse
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = (
            self.env["hr.payroll.structure"].browse(structure_ids).get_all_rules()
        )
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env["hr.salary.rule"].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + "-" + str(contract.id)
                localdict["result"] = None
                localdict["result_qty"] = 1.0
                localdict["result_rate"] = 100
                p = payslip.pay_type == "fix" and payslip.mid_percentage or 0.0
                # check if the rule can be applied
                if rule.satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule.compute_rule(localdict)
                    # probuse start-----------------------
                    if (payslip.pay_type == "fix" or p) and p > 0.00:
                        if rule.code == "GROSS" or rule.code == "NET":
                            pass
                        # if working days based on start and end date pass it no need to change amount
                        elif rule.quantity.find("worked_days") != -1:
                            pass
                        else:
                            amount = amount * p / 100
                    if (
                        rule.code == "TAXPAYFIRST"
                    ):  # 25 oct 2013 # Persnal allwonce wil calc from here only
                        # That line called PERSONAL ALLOW means we will compare 1% of Gross with 200000 and take the higher figure. Then add 20% of Gross Income to this. This will give us the figure for Personal Allowance
                        # Compare 1% of Gross * 12 with N200000 and take the higher figure. Then add 20% of Gross Income * 12. This will give the Personal Allowance Line
                        one_gross = (store_gross * 0.01) * 12
                        if amount > one_gross:
                            figure = amount
                        else:
                            figure = one_gross
                        #                        figure = figure + ((store_gross * 0.20) * 12)
                        amount = figure
                    #                        rate = 100
                    if rule.code == "PAYPERMONTH" and amount < 0:  # b
                        a = -amount
                        if (store_gross * 0.01) > a:
                            amount = -(store_gross * 0.01)

                    if (
                        rule.code == "PERNG"
                    ):  # 25 oct 2013 # Persnal allwonce wil calc from here only
                        # That line called PERSONAL ALLOW means we will compare 1% of Gross with 200000 and take the higher figure. Then add 20% of Gross Income to this. This will give us the figure for Personal Allowance
                        # Compare 1% of Gross * 12 with N200000 and take the higher figure. Then add 20% of Gross Income * 12. This will give the Personal Allowance Line
                        one_gross = (store_gross * 0.01) * 12
                        fix = 200000
                        if fix > one_gross:
                            figure = fix
                        else:
                            figure = one_gross
                        figure = figure + ((store_gross * 0.20) * 12)
                        amount = -figure
                        # probuse end-----------------------

                    # check if there is already a rule computed with that code
                    previous_amount = (
                        rule.code in localdict and localdict[rule.code] or 0.0
                    )
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = 0.0  # probuse
                    if amount and qty and rate:  # probuse
                        tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(
                        localdict, rule.category_id, tot_rule - previous_amount
                    )
                    # create/overwrite the rule in the temporary results
                    if rule.code == "GROSS":  # probuse
                        store_gross = amount  # probuse
                    result_dict[key] = {
                        "salary_rule_id": rule.id,
                        "contract_id": contract.id,
                        "name": rule.name,
                        "code": rule.code,
                        "category_id": rule.category_id.id,
                        "sequence": rule.sequence,
                        "appears_on_payslip": rule.appears_on_payslip,
                        "condition_select": rule.condition_select,
                        "condition_python": rule.condition_python,
                        "condition_range": rule.condition_range,
                        "condition_range_min": rule.condition_range_min,
                        "condition_range_max": rule.condition_range_max,
                        "amount_select": rule.amount_select,
                        "amount_fix": rule.amount_fix,
                        "amount_python_compute": rule.amount_python_compute,
                        "amount_percentage": rule.amount_percentage,
                        "amount_percentage_base": rule.amount_percentage_base,
                        "register_id": rule.register_id.id,
                        "amount": amount,
                        "employee_id": contract.employee_id.id,
                        "quantity": qty,
                        "rate": rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]
        result = [value for code, value in result_dict.items()]
        gross = 0.0  # probuse
        for pline in result:  # probuse
            if pline["code"] == "GROSS":  # probuse
                gross = pline["amount"]  # probuse
        return result
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.env["hr.payslip"]
        inputs_obj = self.env["hr.payslip.worked_days"]
        obj_rule = self.env["hr.salary.rule"]
        payslip = payslip_obj.browse(payslip_id)

        worked_days = {}
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days[worked_days_line.code] = worked_days_line

        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line

    @api.model
    def create(self, vals):
        pays = self.search(
            [
                ("employee_id", "=", vals["employee_id"]),
                ("date_from", "=", vals["date_from"]),
                ("date_to", "=", vals["date_to"]),
            ]
        )
        if vals.get("struct_id", False):
            structure = self.env["hr.payroll.structure"].browse(vals["struct_id"])
            if structure.state == "approve":
                pass
            else:
                raise Warning(
                    _(
                        "You can not create Paysip(s) as Salary Structure still need to approve by authorize person."
                    )
                )
        if vals.get("company_id", False):
            company = self.env["res.company"].browse(vals["company_id"]).no_payroll_run
            if len(pays) > company:
                raise Warning(
                    _(
                        "You are running payroll more than the setting on the configuration of company"
                    )
                )
                pass
        return super(hr_payslip, self).create(vals)

    def compute_sheet(self):
        context = self._context or {}
        if context.get("bonus", False):
            slip_line_pool = self.env["hr.payslip.line"]
            sequence_obj = self.env["ir.sequence"]
            for payslip in self:
                number = payslip.number or sequence_obj.get("salary.slip")
                old_slipline_ids = slip_line_pool.search([("slip_id", "=", payslip.id)])

                if old_slipline_ids:
                    old_slipline_ids.unlink()
                if payslip.contract_id:
                    contract_ids = [payslip.contract_id.id]
                else:
                    contract_ids = self.get_contract(
                        payslip.employee_id, payslip.date_from, payslip.date_to
                    )
                lines = [
                    (0, 0, line)
                    for line in payslip.get_payslip_lines(contract_ids, payslip.id)
                ]
                pay = False
                for line in lines:
                    if context.get("base", "basic"):
                        if context.get("merge", True):
                            if line[2].get("code") == context.get("base"):
                                line[2]["quantity"] = line[2]["quantity"] + 1
                            elif (
                                context.get("base") == "gross_per"
                                and line[2].get("code") == "GROSS"
                            ):
                                line[2]["amount"] += line[2]["amount"] * context.get(
                                    "percent", "1.0"
                                )
                            elif (
                                context.get("base") == "net_per"
                                and line[2].get("code") == "NET"
                            ):
                                line[2]["amount"] += line[2]["amount"] * context.get(
                                    "percent", "1.0"
                                )
                        else:
                            if line[2].get("code") == context.get("base"):
                                pay = line
                            elif (
                                context.get("base") == "gross_per"
                                and line[2].get("code") == "GROSS"
                            ):
                                percent_line = {}
                                percent_line.update(line[2])
                                percent_line.update(
                                    {
                                        "amount": percent_line["amount"]
                                        * context.get("percent", "1.0")
                                    }
                                )
                                pay = (0, 0, percent_line)
                            elif (
                                context.get("base") == "net_per"
                                and line[2].get("code") == "NET"
                            ):
                                percent_line = {}
                                percent_line.update(line[2])
                                percent_line.update(
                                    {
                                        "amount": percent_line["amount"]
                                        * context.get("percent", "1.0")
                                    }
                                )
                                pay = (0, 0, percent_line)
                if not context.get("merge") and pay:
                    lines.append(pay)
                payslip.write(
                    {"line_ids": lines, "number": number,}
                )
        else:
            return super(hr_payslip, self).compute_sheet()
        return True

    def copy(self, default={}):
        if not default:
            default = {}
        default.update({"advice_id": False})
        return super(hr_payslip, self).copy(default)


# class hr_payslip_employees(models.TransientModel):
#     _inherit = "hr.payslip.employees"

#     def compute_sheet(self):
#         payslips = self.env["hr.payslip"]
#         [data] = self.read()
#         active_id = self.env.context.get("active_id")
#         if active_id:
#             [run_data] = (
#                 self.env["hr.payslip.run"]
#                 .browse(active_id)
#                 .read(
#                     [
#                         "date_start",
#                         "date_end",
#                         "credit_note",
#                         "pay_type",
#                         "old_percentage",
#                         "mid_percentage",
#                         "journal_id",
#                         "struct_id",
#                     ]
#                 )
#             )
#         from_date = run_data.get("date_start")
#         to_date = run_data.get("date_end")
#         if not data["employee_ids"]:
#             raise UserError(_("You must select employee(s) to generate payslip(s)."))
#         for employee in self.env["hr.employee"].browse(data["employee_ids"]):
#             slip_data = self.env["hr.payslip"]._onchange_employee()
#             res = {
#                 "employee_id": employee.id,
#                 "name": slip_data["value"].get("name"),
#                 "struct_id": slip_data["value"].get("struct_id"),
#                 "contract_id": slip_data["value"].get("contract_id"),
#                 "payslip_run_id": active_id,
#                 "input_line_ids": [(0, 0, x) for x in slip_data["value"].get("input_line_ids")],
#                 "worked_days_line_ids": [(0, 0, x) for x in slip_data["value"].get("worked_days_line_ids")],
#                 "date_from": from_date,
#                 "date_to": to_date,
#                 "credit_note": run_data.get("credit_note"),
#                 "pay_type": run_data["pay_type"],  # probuse
#                 "old_percentage": run_data["old_percentage"],  # probuse
#                 "mid_percentage": run_data["mid_percentage"],  # probuse
#                 "journal_id": run_data["journal_id"][0],  # probuse
#                 # probuse
#                 "struct_id": run_data["struct_id"]
#                 and run_data["struct_id"][0]
#                 or slip_data["value"]["struct_id"]
#                 or False,
#             }
#             payslips += self.env["hr.payslip"].create(res)
#         payslips.compute_sheet()
#         return {"type": "ir.actions.act_window_close"}
