# -*- encoding: utf-8 -*-

from odoo import api, models, fields
import time
import datetime
from datetime import date
from datetime import datetime, date, time, timedelta
from odoo.fields import Date, Datetime
import logging

class ReportLibroSalarios(models.AbstractModel):
    _name = 'report.rrhh.libro_salarios'

    def _get_contrato(self,id):
        contract = False
        contrato_id = self.env['hr.contract'].search([['employee_id', '=', id]])
        if len(contrato_id) > 1:
            for contrato in contrato_id:
                if contrato.state == 'open':
                    contract = contrato
        else:
            contract = contrato_id
        return {'fecha_ingreso':contract.date_start,'fecha_finalizacion': contract.date_end}

    def _get_empleado(self,id):
        empleado_id = self.env['hr.employee'].search([['id', '=', id]])
        empleado = 0
        if empleado_id:
            empleado = empleado_id
        else:
            empleado_id = self.env['hr.employee'].search([['id', '=', id],['active', '=', False]])
            empleado = empleado_id
        return empleado

    def dias_trabajados(self,employee_id,nomina_id):
        contracts = False
        dias = 0
        if employee_id.contract_id:
            contracts = employee_id.contract_id
        tipos_ausencias_ids = self.env['hr.leave.type'].search([])
        ausencias_restar = []
        dias_ausentados_restar = 0
        for ausencia in tipos_ausencias_ids:
            if ausencia.work_entry_type_id and ausencia.work_entry_type_id.descontar_nomina:
                ausencias_restar.append(ausencia.name)
        for dias in nomina_id.worked_days_line_ids:
            if dias.code in ausencias_restar:
                dias_ausentados_restar += dias.number_of_days
        if contracts.date_start and nomina_id.date_from <= contracts.date_start <= nomina_id.date_to:
            dias_laborados = employee_id._get_work_days_data(Datetime.from_string(contracts.date_start), Datetime.from_string(nomina_id.date_to), calendar=contracts.resource_calendar_id)
            dias = (dias_laborados['days'] + 1 - dias_ausentados_restar) if (dias_laborados['days'] + 1 - dias_ausentados_restar) >= 30 else 30
        elif contracts.date_end and nomina_id.date_from <= contracts.date_end <= nomina_id.date_to:
            dias_laborados = employee_id._get_work_days_data(Datetime.from_string(nomina_id.date_from), Datetime.from_string(contracts.date_end), calendar=contracts.resource_calendar_id)
            dias = (dias_laborados['days'] + 1 - dias_ausentados_restar) if (dias_laborados['days'] + 1 - dias_ausentados_restar) <= 30 else 30
        else:
            if contracts.schedule_pay == 'monthly':
                dias = 30 - dias_ausentados_restar
            if contracts.schedule_pay == 'bi-monthly':
                dias = 15 - dias_ausentados_restar
        return dias

    def _get_dias_laborados_netos(self,empleado,fecha_inicio,fecha_fin):
        work = -1
        trabajo = -1
        dias_trabajados = 0
        nominas = self.env['hr.payslip'].search([['employee_id','=',empleado.id],['date_from', '>=', fecha_inicio],['date_to','<=',fecha_fin]])
        for nomina in nominas:
            for linea in nomina.worked_days_line_ids:
                if linea.number_of_days > 31:
                    contiene_bono = True
                if linea.work_entry_type_id.code == 'TRABAJO100':
                    trabajo = linea.number_of_days
                elif linea.work_entry_type_id.code == 'WORK100':
                    work = linea.number_of_days
            if trabajo >= 0:
                dias_trabajados += trabajo
            else:
                dias_trabajados += work
        return dias_trabajados

    def _get_domingos_trabajados(self,fecha_inicio,fecha_fin):
        cantidad_domingos = 0
        contador = 0
        fecha_desde =  datetime.strptime(str(fecha_inicio),"%Y-%m-%d")
        fecha_hasta = datetime.strptime(str(fecha_fin),"%Y-%m-%d")
        now = datetime.now()
        cantidad_dias = fecha_hasta - fecha_desde
        cantidad_dias = cantidad_dias.days
        dias_a_trabajar = 0
        while (contador <= cantidad_dias):
            otro_tiempo  = fecha_desde + timedelta(days = contador)
            if (otro_tiempo.strftime("%A") == 'Sunday'):
                cantidad_domingos += 1
            contador +=1
        return cantidad_domingos

    def _get_nominas(self,id,anio):
        nomina_id = self.env['hr.payslip'].search([['employee_id', '=', id]],order="date_to asc")
        nominas_lista = []
        numero_orden = 0
        for nomina in nomina_id:
            nomina_anio = int(datetime.strptime(str(nomina.date_to),'%Y-%m-%d').date().strftime('%Y'))
            contiene_bono = False
            if anio == nomina_anio:
                salario = 0
                dias_trabajados = 0
                ordinarias = 0
                extra_ordinarias = 0
                ordinario = 0
                extra_ordinario = 0
                igss = 0
                isr = 0
                anticipos = 0
                bonificacion = 0
                bono = 0
                aguinaldo = 0
                indemnizacion = 0
                septimos_asuetos = 0
                vacaciones = 0
                decreto = 0
                fija = 0
                variable = 0
                otras_deducciones = 0
                otros_salarios = 0
                boni_incentivo_decreto = 0
                dev_isr_otro = 0
                work = -1
                trabajo = -1
                dias_calculados = self.dias_trabajados(nomina.employee_id,nomina)
                dias_laborados = nomina.employee_id._get_work_days_data(Datetime.from_string(nomina.date_from), Datetime.from_string(nomina.date_to), calendar=nomina.employee_id.contract_id.resource_calendar_id)
                dias_laborados_netos = 0
                if dias_laborados['days'] > 60:
                    dias_laborados_netos = self._get_dias_laborados_netos(nomina.employee_id,nomina.date_from,nomina.date_to)
                for linea in nomina.worked_days_line_ids:
                    if linea.number_of_days > 31:
                        contiene_bono = True
                    if linea.work_entry_type_id.code == 'TRABAJO100':
                        trabajo = linea.number_of_days
                    elif linea.work_entry_type_id.code == 'WORK100':
                        work = linea.number_of_days
                if trabajo >= 0:
                    dias_trabajados += trabajo
                else:
                    dias_trabajados += work
                for linea in nomina.line_ids:
                    if linea.salary_rule_id.id in nomina.company_id.salario_ids.ids:
                        salario += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.extras_ordinarias_ids.ids:
                        for entrada in nomina.input_line_ids:
                            if linea.code == entrada.code:
                                extra_ordinarias += entrada.amount
                    if linea.salary_rule_id.id in nomina.company_id.ordinario_ids.ids:
                        ordinario += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.extra_ordinario_ids.ids:
                        extra_ordinario += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.igss_ids.ids:
                        igss += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.isr_ids.ids:
                        isr += linea.total
                        # otras_deducciones += isr
                    if linea.salary_rule_id.id in nomina.company_id.anticipos_ids.ids:
                        anticipos += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.bonificacion_ids.ids:
                        bonificacion += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.bono_ids.ids and contiene_bono:
                        bono += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.aguinaldo_ids.ids and contiene_bono:
                        aguinaldo += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.indemnizacion_ids.ids:
                        indemnizacion += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.vacaciones_ids.ids:
                        vacaciones += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.decreto_ids.ids:
                        decreto += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.fija_ids.ids:
                        fija += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.variable_ids.ids:
                        variable += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.otro_salario_ids.ids:
                        otros_salarios += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.boni_incentivo_decreto_ids.ids:
                        boni_incentivo_decreto += linea.total
                    if linea.salary_rule_id.id in nomina.company_id.devolucion_isr_otro_ids.ids:
                        dev_isr_otro += linea.total

                dias_trabajados = int(dias_laborados_netos) if dias_laborados_netos > 0 else int(dias_trabajados)
                ordinarias = dias_trabajados*8 if dias_trabajados <= 31 else 0
                domingos = self._get_domingos_trabajados(nomina.date_from,nomina.date_to)
                sueldo_diario = 0
                if dias_trabajados > 0:
                    sueldo_diario = salario/30
                else:
                    sueldo_diario = 0

                if dias_trabajados > 31:
                    dias_trabajados = (datetime.strptime(str(nomina.date_to), "%Y-%m-%d") - datetime.strptime(str(nomina.date_from), "%Y-%m-%d")).days
                septimos_asuetos = sueldo_diario * domingos
                ordinario_final = ordinario - septimos_asuetos
                ordinario = ordinario_final
                # total_descuentos = igss + isr + anticipos
                otras_deducciones = anticipos
                total_deducciones = igss + otras_deducciones + isr
                bono_agui_indem = bono + aguinaldo + indemnizacion
                numero_orden += 1
                total_salario_devengado =  ordinario + extra_ordinario + septimos_asuetos + vacaciones + otros_salarios
                nominas_lista.append({
                    'orden': numero_orden,
                    'fecha_inicio': nomina.date_from,
                    'fecha_fin': nomina.date_to,
                    'moneda_id': nomina.company_id.currency_id,
                    'salario': salario,
                    'dias_trabajados': dias_trabajados,
                    'dias_calculados': int(dias_calculados),
                    'ordinarias': ordinarias,
                    'extra_ordinarias': extra_ordinarias,
                    'ordinario': ordinario,
                    'extra_ordinario': extra_ordinario,
                    'septimos_asuetos': septimos_asuetos,
                    'vacaciones': vacaciones,
                    'total_salario_devengado': total_salario_devengado,
                    'igss': igss,
                    'isr': isr,
                    'anticipos': anticipos,
                    'otras_deducciones': otras_deducciones,
                    'total_deducciones': total_deducciones,
                    'bonificacion_id': bonificacion,
                    # 'decreto': decreto,
                    'boni_incentivo_decreto': boni_incentivo_decreto,
                    # 'fija': fija,
                    'variable': variable,
                    'dev_isr_otro': dev_isr_otro,
                    'bono_agui_indem': bono_agui_indem,
                    'otros_salarios': otros_salarios,
                    # 'liquido_recibir': total_salario_devengado + boni_incentivo_decreto +dev_isr_otro
                    'liquido_recibir': total_salario_devengado + total_deducciones +bono_agui_indem+ boni_incentivo_decreto + dev_isr_otro
                    # 'liquido_recibir': total_salario_devengado + total_deducciones + bono_agui_indem + decreto + fija + variable
                })
        return nominas_lista

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
            '_get_empleado': self._get_empleado,
            '_get_contrato': self._get_contrato,
            '_get_nominas': self._get_nominas,
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
