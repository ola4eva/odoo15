from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=[("director", "Approved")])

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
            self.message_post(body=body, subject=subject, partner_ids=partner_ids)
        return True

    def action_md_approve(self):
        invoices = self.order_line.invoice_lines.move_id.filtered(
            lambda r: r.move_type in ("out_invoice", "out_refund")
        )
        states = invoices.mapped("payment_state")
        in_payment = all([state == "in_payment" for state in states])
        if not in_payment:
            raise UserError(
                """Kindly wait for the accounting department to confirm the customer payment before you can approve."""
            )

        self.write({"state": "director"})
