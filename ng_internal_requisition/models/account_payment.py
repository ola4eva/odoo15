from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        body = "Sale Order Approval"
        subject = """<p>Hi!</p>
            <p>This order payment has been confirmed by the accounting department and it is waiting for you approval"""
        origin = self.invoice_origin
        order = self.env["sale.order"].search([("name", "=", origin)], limit=1)
        if order:
            order.notify(
                body, subject, group="ng_internal_requisition.group_managing_director"
            )
        return super(AccountMove, self).action_post()
