# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
import logging

class rrhh_cerrar_nominas_wizard(models.TransientModel):
    _name = 'rrhh.cerrar_nominas.wizard'

    def cerrar_nominas(self):
        if self.env.context.get('active_ids', []):
            for payslip in self.env['hr.payslip'].browse(self.env.context.get('active_ids', [])):
                if payslip.state == 'draft':
                    payslip.action_payslip_done()

        return {'type': 'ir.actions.act_window_close'}
