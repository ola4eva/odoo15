from odoo import api, fields, models, _


class hr_contract(models.Model):
    """Employee contract allows to add different values in fields.

    Fields are used in salary rule computation.
    """

    _inherit = "hr.contract"
    _description = "HR Contract"

    leave_allow_day = fields.Float(
        string="Earned Leave Allowance (Amount)",
        help="Please specify Earned leave allowance per day for employee which will be use "
        "while deducting from salary for unapproved leaves.",
    )
    pension_company = fields.Float(
        string="PAYE(amount)",
        help="Please give % between 0-100 for Pension from Company Contribution.",
        default=0,
        required=True,
    )
    pension_employee = fields.Float(
        string="CTCS Deduction (amount)",
        help="Employee Contribution for Pension in % between 0-100.",
        default=0,
    )
    hra = fields.Float(
        string="House Rent Allowance (%)",
        digits="Payroll",
        help="""HRA is an allowance given by the employer to the employee for taking care of his rental 
                       or accommodation expenses, Please specify % between 0-100 for HRA given to Employee.""",
        default=75.0,
    )

    # contract_type =  fields.Char()

    def onchange_employee_id(self):
        """Pick the corresponding job_id for selected employee"""
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id

    template_id = fields.Many2one("salary.template", string="Salary Template")
    # payroll fields to track
    # basic = fields.Float(string="Basic", readonly=True, compute="_compute_field_value", store=True)
    # housing = fields.Float(string="Housing", readonly=True, compute="_compute_field_value", store=True)
    # leave_allowance = fields.Float(string="Leave Allowance", readonly=True, compute="_compute_field_value", store=True)
    # meal = fields.Float(string="Meal", readonly=True, compute="_compute_field_value", store=True)
    # furniture = fields.Float(string="Furniture", readonly=True, compute="_compute_field_value", store=True)
    # domestic = fields.Float(string="Domestic", readonly=True, compute="_compute_field_value", store=True)
    # travelling = fields.Float(string="Entertainment", readonly=True, compute="_compute_field_value", store=True)
    # others = fields.Float(string="Others", readonly=True, compute="_compute_field_value", store=True)
    # extra = fields.Float(string="Msub", readonly=True, compute="_compute_field_value", store=True)
    # transport = fields.Float(string="Transport", readonly=True, compute="_compute_field_value", store=True)
    # utility = fields.Float(string="Utility", readonly=True, compute="_compute_field_value", store=True)

    # # Relational fields

    # # Newly added fields
    # rural_posting = fields.Float(string="Rural Posting", readonly=True, compute="_compute_field_value", store=True)
    # shift_allowance = fields.Float(string="HM", readonly=True, compute="_compute_field_value", store=True)
    # hazard = fields.Float(string="Driver", readonly=True, compute="_compute_field_value", store=True)
    # call_duty_all = fields.Float(string="Security", readonly=True, compute="_compute_field_value", store=True)
    # extra_two = fields.Float(string="Extra 2", readonly=True, compute="_compute_field_value", store=True)

    # @api.depends("template_id")
    # def _compute_field_value(self, context={}):
    #     impacted_fields = [
    #         "basic",
    #         "housing",
    #         "transport",
    #         "leave_allowance",
    #         "furniture",
    #         "domestic",
    #         "travelling",
    #         "others",
    #         "extra",
    #         "utility",
    #         "meal",
    #         "rural_posting",
    #         "shift_allowance",
    #         "hazard",
    #         "call_duty_all",
    #         "extra_two",
    #     ]

    #     for contract in self:
    #         if contract.template_id:
    #             for field in impacted_fields:
    #                 contract[field] = contract.template_id[field]
    #         else:
    #             for field in impacted_fields:
    #                 contract[field] = contract[field]

    # @api.model
    # def create(self, values):
    #     return super(hr_contract, self).create(values)
