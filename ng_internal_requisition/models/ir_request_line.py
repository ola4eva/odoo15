from datetime import datetime
from odoo import models, fields, api, _


class IRRequestApprove(models.Model):
    _name = "ng.ir.request.line"
    _description = "ng.ir.request.line"

    request_id = fields.Many2one(comodel_name="ng.ir.request", string="Request")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    quantity = fields.Float(string="Quantity", default=1.0)
    uom_id = fields.Many2one(
        comodel_name="uom.uom", string="UOM", related="product_id.uom_id", store=True
    )
