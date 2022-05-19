from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    bill_type = fields.Selection(
        selection=[("normal", "Regular Order"), ("service", "Service Order")],
        default="normal",
        string="Bill Type",
        required=True,
    )
    is_complete_job = fields.Boolean(string="Job Complete")
    is_service_order = fields.Boolean(string="Service Order")

    def action_create_invoice(self):
        if self.message_attachment_count == 0 and self.is_service_order == True:
            raise ValidationError(
                """For service Order, you need to attach the required document in the chatter before supplier invoice can be generated."""
            )
        return super(PurchaseOrder, self).action_create_invoice()

    @api.onchange("is_service_order")
    def _onchange_is_service_order(self):
        for rec in self:
            if rec.is_service_order:
                rec.bill_type = "service"
            else:
                rec.bill_type = "normal"

    @api.onchange("bill_type")
    def _onchange_bill_type(self):
        for rec in self:
            if rec.bill_type == "service":
                rec.is_service_order = True
            else:
                rec.is_service_order = False
