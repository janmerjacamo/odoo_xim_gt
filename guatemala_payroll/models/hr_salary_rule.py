
from odoo import models, fields

class HrPayrollGuatemala(models.Model):
    _inherit = 'hr.salary.rule'

    is_guatemala_rule = fields.Boolean(string="Guatemala Payroll Rule", default=False)

