# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class rrhh_libro_salarios(models.TransientModel):
    _name = 'rrhh.libro_salarios'

    anio = fields.Integer('Año', required=True)

    def print_report(self):
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(['anio'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref('rrhh.action_libro_salarios').report_action([], data=datas)
