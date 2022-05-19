from odoo import api, fields, models, _


class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"

    def generate_random_barcode(self):
        for employee in self:
            employee.barcode = self.env["ir.sequence"].next_by_code("navante.badge")
