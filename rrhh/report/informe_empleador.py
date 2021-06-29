# -*- encoding: utf-8 -*-

from odoo import api, models, fields
import time
import datetime
from datetime import date
from datetime import datetime, date, time
import logging

class ReportInformeEmpleador(models.AbstractModel):
    _name = 'report.rrhh.informe_empleador'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        self.model = 'hr.employee'
        docs = data.get('ids', data.get('active_ids'))
        anio = data.get('form', {}).get('anio', False)

        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'docs': docs,
            'anio': anio,
            'datos_compania': datos_compania,
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
