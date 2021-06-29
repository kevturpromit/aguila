# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class account_payment(models.Model):
    _inherit = "account.payment"

    nomina_id = fields.Many2one('hr.payslip','Nomina')
