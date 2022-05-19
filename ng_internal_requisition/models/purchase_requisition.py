from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    requisition_id = fields.Many2one(comodel_name="ng.ir.request")

    def action_open(self):
        condition = bool(self.requisition_id.id) == True and len(self.purchase_ids) >= 1
        if bool(self.requisition_id.id) == True and not condition:
            raise UserError(
                """Quotations should be raised or sent to mimimum of 3 vendors."""
            )
        else:
            self.requisition_id.procurement_approve_done(self)
        self.write({"state": "open"})
