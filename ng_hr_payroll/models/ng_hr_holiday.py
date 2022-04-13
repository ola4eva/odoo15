from odoo import models, fields, api, _


class hr_holidays(models.Model):
    _inherit = "hr.leave"
    _description = "Leave"

    carry_fw = fields.Boolean(
        string="Carry Forward",
        readonly=True,
        help="Tick if you want to include this types of leave to carry forward next year. Only legal leaves can be carried forward.",
    )
    carry_fw_ded = fields.Boolean(
        string="Carry forward deduction",
        help="This field is when you carry forward leaves legal leaves need to set zero for that we need to create leave request for that to set it zero..",
        default=False,
    )
    carry_fw_allocation = fields.Boolean(
        string="Is Carry Forwarded?", default=False
    )  # see help in xml file .

    policy = fields.Selection(
        selection=[
            ("earned", "Deduct From Earned Leaves"),
            ("payslip", "Deduct From Salary"),
        ],
        string="Leave Deduction",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)], "confirm": [("readonly", False)]},
        help="Deduct from salary allows you put leaves amount deduction on salary while Deduct from Earned leaves will simple use your earned leaves or allocated leaves.",
        default="earned",
    )
