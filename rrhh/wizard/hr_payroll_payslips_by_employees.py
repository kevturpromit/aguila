# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def _get_employees(self):
        res = super(HrPayslipEmployees, self)._get_employees()
        return False
