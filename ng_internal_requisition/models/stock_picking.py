from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    state = fields.Selection(selection_add=[("director", "Director")])

    def button_validate(self):
        if self.sale_id and self.sale_id.mapped("state") != "director":
            raise UserError(
                """The managing director needs to approve the sale's order before you can send the item out to the customer"""
            )
        return super(StockPicking, self).button_validate()
