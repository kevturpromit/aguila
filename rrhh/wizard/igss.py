# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
import time
import base64
import io
import logging
import datetime
from datetime import datetime

class rrhh_igss_wizard(models.TransientModel):
    _name = 'rrhh.igss.wizard'

    def _default_payslip_run(self):
        if len(self.env.context.get('active_ids', [])) > 0:
            nominas = self.env['hr.payslip.run'].search([('id','in',self.env.context.get('active_ids'))])
            return nominas
        else:
            return None

    payslip_run_id = fields.Many2many('hr.payslip.run', string='Payslip run',default=_default_payslip_run)
    archivo = fields.Binary('Archivo')
    name =  fields.Char('File Name', size=32)
    identificacion_tipo_planilla = fields.Char('Identificación tipo de planilla')
    nombre_tipo_planilla = fields.Char('Nombre tipo de planilla')
    tipo_afiliados = fields.Char('Tipo de afiliado')
    periodo_planilla = fields.Char('Periodo de planilla')
    departamento_republica = fields.Char('Departamento de la república donde laboran los empleados ')
    actividad_economica = fields.Char('Actividad económica')
    clase_planilla = fields.Char('Clase de planilla')
    numero_liquidacion = fields.Char('Numero de liquidacion')
    tipo_planilla_liquidacion = fields.Char('Tipo de planilla de liquidación')
    fecha_inicial = fields.Date('Fecha inicial liquidación')
    fecha_final = fields.Date('Fecha final de liquidación')
    tipo_liquidacion = fields.Char('Tipo de liquidación')
    numero_nota_cargo = fields.Char('Número nota de cargo')

    def generar(self):
        datos = ''
        for w in self:
            datos += str(w.payslip_run_id[0].slip_ids[0].company_id.version_mensaje) + '|' + str(datetime.today().strftime('%d/%m/%Y')) + '|' + str(w.payslip_run_id[0].slip_ids[0].company_id.numero_patronal) + '|'+ str(datetime.strptime(str(w.payslip_run_id[0].date_start),'%Y-%m-%d').date().strftime('%m')).lstrip('0')+ '|' + str(datetime.strptime(str(w.payslip_run_id[0].date_start),'%Y-%m-%d').date().strftime('%Y')).lstrip('0') + '|' + str(w.payslip_run_id[0].slip_ids[0].company_id.name) + '|' +str(w.payslip_run_id[0].slip_ids[0].company_id.vat) + '|'+ str(w.payslip_run_id[0].slip_ids[0].company_id.email) + '|' + str(w.payslip_run_id[0].slip_ids[0].company_id.tipo_planilla) + '\r\n'
            datos += '[centros]' + '\r\n'
            for centro in w.payslip_run_id[0].slip_ids[0].company_id.centro_trabajo_ids:
                datos += str(centro.codigo) + '|' + str(centro.nombre) + '|' + str(centro.direccion) + '|' + str(centro.zona) + '|' + str(centro.telefono) + '|' + str(centro.fax) + '|' + str(centro.nombre_contacto) + '|' + str(centro.correo_electronico) + '|' + str(centro.codigo_departamento) + '|' + str(centro.codigo_municipio) + '|' + str(centro.codigo_actividad_economica) + '\r\n'
            datos += '[tiposplanilla]' + '\r\n'
            datos += self.identificacion_tipo_planilla + '|' + self.nombre_tipo_planilla + '|' + self.tipo_afiliados + '|' + self.periodo_planilla + '|' + self.departamento_republica + '|' + self.actividad_economica + '|' + self.clase_planilla + '|' +'\r\n'
            datos += '[liquidaciones]' + '\r\n'
            datos += self.numero_liquidacion + '|' + self.tipo_planilla_liquidacion + '|' + str(datetime.strptime(str(self.fecha_inicial),'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|' + str(datetime.strptime(str(self.fecha_final),'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|' + self.tipo_liquidacion + '|' + (self.numero_nota_cargo if self.numero_nota_cargo else '') + '|' +'\r\n'
            datos += '[empleados]' + '\r\n'
            empleados = {}
            suspensiones = []
            for payslip_run in w.payslip_run_id:
                for slip in payslip_run.slip_ids:
                    if slip.contract_id:
                        if slip.employee_id.id not in empleados:
                            empleados[slip.employee_id.id] = {'empleado_id': slip.employee_id.id,'informacion': [0] * 15,'suspension': ''}

                        contrato_ids = self.env['hr.contract'].search( [['employee_id', '=', slip.employee_id.id]],offset=0,limit=1,order='date_start desc')
                        numero_liquidacion = str(slip.employee_id.numero_liquidacion) if slip.employee_id.numero_liquidacion else ''
                        numero_afiliado = str(slip.employee_id.igss) if slip.employee_id.igss else ''
                        primer_nombre = str(slip.employee_id.primer_nombre) if slip.employee_id.primer_nombre else ''
                        segundo_nombre = str(slip.employee_id.segundo_nombre) if slip.employee_id.segundo_nombre else ''
                        primer_apellido = str(slip.employee_id.primer_apellido) if slip.employee_id.primer_apellido else ''
                        segundo_apellido = str(slip.employee_id.segundo_apellido) if slip.employee_id.segundo_apellido else ''
                        apellido_casada = str(slip.employee_id.apellido_casada) if slip.employee_id.apellido_casada else ''
                        sueldo = 0
                        for linea in slip.line_ids:
                            if linea.salary_rule_id.id in slip.employee_id.company_id.igss_ids.ids:
                                sueldo += linea.amount

                        mes_inicio_contrato = datetime.strptime(str(slip.contract_id.date_start), '%Y-%m-%d').month
                        mes_final_contrato = datetime.strptime(str(slip.contract_id.date_end), '%Y-%m-%d').month if slip.contract_id.date_end else ''
                        mes_planilla = datetime.strptime(str(payslip_run.date_start), '%Y-%m-%d').month
                        fecha_alta = str(datetime.strptime(str(slip.contract_id.date_start),'%Y-%m-%d').date().strftime('%d/%m/%Y')) if mes_inicio_contrato == mes_planilla else ''
                        fecha_baja = str(datetime.strptime(str(slip.contract_id.date_end),'%Y-%m-%d').date().strftime('%d/%m/%Y')) if mes_final_contrato == mes_planilla else ''

                        centro_trabajo = str(slip.employee_id.centro_trabajo_id.codigo) if slip.employee_id.centro_trabajo_id else ''
                        nit = str(slip.employee_id.nit) if slip.employee_id.nit else ''
                        codigo_ocupacion = str(slip.employee_id.codigo_ocupacion) if slip.employee_id.codigo_ocupacion else ''
                        condicion_laboral = str(slip.employee_id.condicion_laboral) if slip.employee_id.condicion_laboral else ''
                        deducciones = ''

                        empleados[slip.employee_id.id]['informacion'][0] = (numero_liquidacion)
                        empleados[slip.employee_id.id]['informacion'][1] = (numero_afiliado)
                        empleados[slip.employee_id.id]['informacion'][2] = (primer_nombre)
                        empleados[slip.employee_id.id]['informacion'][3] = (segundo_nombre)
                        empleados[slip.employee_id.id]['informacion'][4] = (primer_apellido)
                        empleados[slip.employee_id.id]['informacion'][5] = (segundo_apellido)
                        empleados[slip.employee_id.id]['informacion'][6] = (apellido_casada)
                        empleados[slip.employee_id.id]['informacion'][7] += sueldo
                        empleados[slip.employee_id.id]['informacion'][8] = (fecha_alta)
                        empleados[slip.employee_id.id]['informacion'][9] = (fecha_baja)
                        empleados[slip.employee_id.id]['informacion'][10] = (centro_trabajo)
                        empleados[slip.employee_id.id]['informacion'][11] = (nit)
                        empleados[slip.employee_id.id]['informacion'][12] = (codigo_ocupacion)
                        empleados[slip.employee_id.id]['informacion'][13] = (condicion_laboral)
                        empleados[slip.employee_id.id]['informacion'][14] = (deducciones)

            if empleados:
                for empleado in empleados.values():
                    for dato in empleado['informacion']:
                        datos += str(dato) + '|'
                    datos += '\r\n'

                    ausencias = self.env['hr.leave'].search([('employee_id','=', empleado['empleado_id']),('request_date_from','>=',self.fecha_inicial),('request_date_to','<=',self.fecha_final),('state','=','validate')])
                    if ausencias:
                        reglas = [x.code for x in slip.employee_id.company_id.igss_ids]
                        for ausencia in ausencias:
                            if ausencia.holiday_status_id.code in reglas:
                                fecha_inicio = str(datetime.strptime(str(ausencia.date_from),'%Y-%m-%d %H:%M:%S').date().strftime('%d/%m/%Y'))
                                fecha_fin = str(datetime.strptime(str(ausencia.date_to),'%Y-%m-%d %H:%M:%S').date().strftime('%d/%m/%Y'))
                                suspensiones.append(numero_liquidacion + '|' + numero_afiliado + '|' + primer_nombre + '|' + segundo_nombre + '|' + primer_apellido + '|' + segundo_apellido + '|' + apellido_casada + '|' + fecha_inicio + '|' + fecha_fin + '|' + '\r\n')

            datos += '[suspendidos]' + '\r\n'
            if suspensiones:
                for suspension in suspensiones:
                    datos += suspension
            datos += '[licencias]' + '\r\n'
            datos += '[juramento]' + '\r\n'
            datos += 'BAJO MI EXCLUSIVA Y ABSOLUTA RESPONSABILIDAD, DECLARO QUE LA INFORMACION QUE AQUI CONSIGNO ES FIEL Y EXACTA, QUE ESTA PLANILLA INCLUYE A TODOS LOS TRABAJADORES QUE ESTUVIERON A MI SERVICIO Y QUE SUS SALARIOS SON LOS EFECTIVAMENTE DEVENGADOS, DURANTE EL MES ARRIBA INDICADO' + '\r\n'
            datos += '[finplanilla]' + '\r\n'
            datos = datos.replace('False', '')
        datos = base64.b64encode(datos.encode("utf-8"))
        self.write({'archivo': datos, 'name':'planilla.txt'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.igss.wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
