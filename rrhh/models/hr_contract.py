# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

class Contract(models.Model):
    _inherit = "hr.contract"

    motivo_terminacion = fields.Selection([
        ('reuncia', 'Renuncia'),
        ('despido', 'Despido'),
        ('despido_justificado', 'Despido Justificado'),
        ], 'Motivo de terminacion')
    base_extra = fields.Monetary('Base Extra', digits=(16,2), track_visibility='onchange')
    wage = fields.Monetary('Wage', digits=(16, 2), required=True, help="Employee's monthly gross wage.",track_visibility='onchange')
    fecha_reinicio_labores = fields.Date('Fecha de reinicio labores')
    temporalidad_contrato = fields.Char('Teporalidad del contrato')
    calcula_indemnizacion = fields.Boolean('Calcula indemnizacion')
