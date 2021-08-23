# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
import logging

class Partner(models.Model):
    _inherit = "res.partner"

    nombre_facturacion_fel = fields.Char('Nombre facturación FEL', copy=False)
