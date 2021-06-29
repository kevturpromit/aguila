# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import xlsxwriter
import base64
import io
import logging
import time
import datetime
from datetime import date
from datetime import datetime, date, time
from odoo.fields import Date, Datetime
import itertools

class rrhh_informe_empleador(models.TransientModel):
    _name = 'rrhh.informe_empleador'

    anio = fields.Integer('Año', required=True)
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

    def empleados_inicio_anio(self,company_id,anio):
        empleados = 0
        empleado_ids = self.env['hr.employee'].search([['company_id', '=', company_id]])
        for empleado in empleado_ids:
            if empleado.contract_ids:
                for contrato in empleado.contract_ids:
                    if contrato.state == 'open':
                        anio_fin_contrato = 0
                        anio_inicio_contrato = contrato.date_start.year
                        if contrato.date_end:
                            anio_fin_contrato = contrato.date_end.year
                        if anio_inicio_contrato < anio and (contrato.date_end == False or anio_fin_contrato < anio) :
                            empleados += 1
        return empleados

    def empleados_fin_anio(self,company_id,anio):
        empleados = 0
        empleado_ids = self.env['hr.employee'].search([['company_id', '=', company_id]])
        for empleado in empleado_ids:
            if empleado.contract_ids:
                for contrato in empleado.contract_ids:
                    if contrato.state == 'open':
                        anio_fin_contrato = 0
                        anio_inicio_contrato = contrato.date_start.year
                        if contrato.date_end:
                            anio_fin_contrato = contrato.date_end.year
                        if anio_inicio_contrato <= anio and (contrato.date_end == False or anio_fin_contrato <= anio) :
                            empleados += 1
        return empleados

    def print_report(self):
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(['anio'])
        res = res and res[0] or {}
        res['anio'] = res['anio']
        datas['form'] = res
        return self.env.ref('rrhh.action_informe_empleador').report_action([], data=datas)

    def dias_trabajados_anual(self,empleado_id,anio):
        anio_inicio_contrato = int(empleado_id.contract_id.date_start.strftime('%Y'))
        anio_inicio = datetime.strptime(str(anio)+'-01'+'-01', '%Y-%m-%d').date().strftime('%Y-%m-%d')
        anio_fin = datetime.strptime(str(anio)+'-12'+'-31', '%Y-%m-%d').date().strftime('%Y-%m-%d')
        dias_laborados = 0
        empleado = self.env['hr.employee'].browse(empleado_id.id)
        if empleado_id.contract_id.date_start and empleado_id.contract_id.date_end:
            anio_fin_contrato = int(empleado_id.contract_id.date_end.strftime('%Y'))
            if anio_inicio_contrato == anio and anio_fin_contrato == anio:
                dias = empleado._get_work_days_data(Datetime.from_string(empleado_id.contract_id.date_start), Datetime.from_string(empleado_id.contract_id.date_end), calendar=empleado_id.contract_id.resource_calendar_id)
                dias_laborados = dias['days']
            if anio_inicio_contrato != anio and anio_fin_contrato == anio:
                dias = empleado._get_work_days_data(Datetime.from_string(anio_inicio), Datetime.from_string(empleado_id.contract_id.date_end), calendar=empleado_id.contract_id.resource_calendar_id)
                dias_laborados = dias['days']
        if empleado_id.contract_id.date_start and empleado_id.contract_id.date_end == False:
            if anio_inicio_contrato == anio:
                dias = empleado._get_work_days_data(Datetime.from_string(empleado_id.contract_id.date_start), Datetime.from_string(anio_fin), calendar=empleado_id.contract_id.resource_calendar_id)
                dias_laborados = dias['days']
            else:
                dias = empleado.get_work_days_data(Datetime.from_string(anio_inicio), Datetime.from_string(anio_fin), calendar=empleado_id.contract_id.resource_calendar_id)
                dias_laborados = dias['days']
        return dias_laborados

    def print_report_excel(self):
        for w in self:
            dict = {}
            empleados_id = self.env.context.get('active_ids', [])
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            dict['anio'] = w['anio']
            empleados_archivados = self.env['hr.employee'].sudo().search([('active','=',False),('id', 'in', empleados_id)])
            empleados_activos = self.env['hr.employee'].sudo().search([('active','=',True),('id', 'in', empleados_id)])
            empleados = empleados_archivados + empleados_activos
            responsable_id = self.env['hr.employee'].sudo().search([['id', '=', self.env.user.id]])
            datos_compania = empleados[0].company_id


            hoja_patrono = libro.add_worksheet('Patrono')
            empleados_inicio_anio = self.empleados_inicio_anio(datos_compania.id,w['anio'])
            empleados_fin_anio = self.empleados_fin_anio(datos_compania.id,w['anio'])
            col_width = 100 * 75
            row_height = 35 * 30

            hoja_patrono.write(6,0,'Datos De Identificación')
            hoja_patrono.write(7,0,'NIT')
            hoja_patrono.write(7,1,datos_compania.vat)
            hoja_patrono.write(8,0,'NOMBRE DE LA EMPRESA')
            hoja_patrono.write(8,1,datos_compania.name)
            hoja_patrono.write(9,0,'NACIONALIDAD DEL EMPLEADOR')
            hoja_patrono.write(9,1,datos_compania.country_id.name)
            hoja_patrono.write(10,0,'DENOMINACION O RAZON SOCIAL DEL PATRONO')
            hoja_patrono.write(10,1,datos_compania.company_registry)
            hoja_patrono.write(11,0,'NUMERO PATRONAL IGSS')
            hoja_patrono.write(11,1,datos_compania.numero_patronal)

            hoja_patrono.write(12,0,'Datos General')
            hoja_patrono.write(13,0,'Barrio O Colonia')
            hoja_patrono.write(13,1,datos_compania.barrio_colonia)
            hoja_patrono.write(13,2,'Zona')
            hoja_patrono.write(13,3,datos_compania.zona_centro_trabajo)
            hoja_patrono.write(14,0,'Calle')
            hoja_patrono.write(14,1,datos_compania.street2)
            hoja_patrono.write(14,2,'Avenida')
            hoja_patrono.write(14,3,datos_compania.street)
            hoja_patrono.write(15,0,'Teléfono')
            hoja_patrono.write(15,1,datos_compania.phone)
            hoja_patrono.write(15,2,'Nomenclatura')
            hoja_patrono.write(15,3,datos_compania.nomenclatura)
            hoja_patrono.write(16,0,'Sitio Web')
            hoja_patrono.write(16,1,datos_compania.website)
            hoja_patrono.write(16,2,'E-Mail')
            hoja_patrono.write(16,3,datos_compania.email)
            hoja_patrono.write(17,0,'Existe Sindicato (SI) O (NO)')
            hoja_patrono.write(17,1,datos_compania.sindicato)

            hoja_patrono.write(19,0,'Ubicación Geográfica')
            hoja_patrono.write(20,0,'País')
            hoja_patrono.write(20,1,datos_compania.country_id.name)
            hoja_patrono.write(20,2,'Región')
            hoja_patrono.write(20,3,datos_compania.state_id.name)
            hoja_patrono.write(21,0,'Departamento')
            hoja_patrono.write(21,1,datos_compania.state_id.name)
            hoja_patrono.write(21,2,'Municipio')
            hoja_patrono.write(21,3,datos_compania.city)
            hoja_patrono.write(22,0,'Datos Económicos')
            hoja_patrono.write(23,0,'Año de Inicio de Operaciones')
            hoja_patrono.write(23,1,datos_compania.anio_inicio_operaciones)
            hoja_patrono.write(24,0,'Cantidad Total de Empleados Inicio de Año ')
            hoja_patrono.write(24,1, empleados_inicio_anio)
            hoja_patrono.write(25,0,'Cantidad Total de Empleados fin de Año')
            hoja_patrono.write(25,1, empleados_fin_anio)
            hoja_patrono.write(26,0,'Tamaño de la empresa por ventas anuales en salarios minimos')
            hoja_patrono.write(26,1, datos_compania.tamanio_empresa_ventas)
            hoja_patrono.write(27,0,'Tamaño de empresa según cantidad de Trabajadores')
            hoja_patrono.write(27,1,datos_compania.tamanio_empresa_trabajadores)
            hoja_patrono.write(28,0,'Tiene planificado contratar nuevo personal (SI) (NO)')
            hoja_patrono.write(28,1,datos_compania.contratar_personal)
            hoja_patrono.write(29,0,'Contabilidad Completa')
            hoja_patrono.write(29,1,datos_compania.contabilidad_completa)

            hoja_patrono.write(31,0,'Actividad Económica Principal')
            hoja_patrono.write(32,0,'Actividad Gran Grupo')
            hoja_patrono.write(32,1,datos_compania.actividad_gran_grupo)
            hoja_patrono.write(33,0,'Actividad Económica')
            hoja_patrono.write(33,1,datos_compania.actividad_economica)
            hoja_patrono.write(34,0,'Sub Actividad Económica')
            hoja_patrono.write(34,1,datos_compania.sub_actividad_economica)
            hoja_patrono.write(35,0,'Ocupación Grupo')
            hoja_patrono.write(35,1,datos_compania.ocupacion_grupo)

            hoja_patrono.write(37,0,'Datos Del Contacto')
            hoja_patrono.write(38,0,'Nombre Del Represéntate. Legal')
            hoja_patrono.write(38,1,datos_compania.representante_legal_id.name)
            hoja_patrono.write(39,0,'Tipo De Documento Del Represéntate. Legal ')
            hoja_patrono.write(39,1,'DPI')
            hoja_patrono.write(40,0,'Nombre Jefe De Recursos Humanos')
            hoja_patrono.write(40,1,datos_compania.jefe_recursos_humanos_id.name)
            hoja_patrono.write(41,0,'No. De Identificación De  Jefe De RR.HH.')
            hoja_patrono.write(41,1,datos_compania.jefe_recursos_humanos_id.identification_id)
            hoja_patrono.write(42,0,'E-Mail Del Jefe RR.HH.')
            hoja_patrono.write(42,1,datos_compania.jefe_recursos_humanos_id.work_email)
            hoja_patrono.write(43,0,'E-Mail Del Responsable Del Informe ')
            hoja_patrono.write(43,1,responsable_id.work_email)
            hoja_patrono.write(44,0,'Teléfono Del Represéntate Del Informe')
            hoja_patrono.write(44,1,responsable_id.work_phone)
            hoja_patrono.write(45,0,'Nacionalidad Del Representante Legal')
            hoja_patrono.write(45,1, datos_compania.representante_legal_id.country_id.name)
            hoja_patrono.write(46,0,'No. De Identificación Del Represéntate Legal')
            hoja_patrono.write(46,1, datos_compania.representante_legal_id.identification_id)
            hoja_patrono.write(47,0,'Tipo De Documentación Del Jefe De RR.HH.')
            hoja_patrono.write(47,1, 'DPI')
            hoja_patrono.write(48,0,'Teléfono Jefe RR.HH.')
            hoja_patrono.write(48,1, datos_compania.jefe_recursos_humanos_id.work_phone)
            hoja_patrono.write(49,0,'Nombre Del Represéntate de Elaborar el Informe Del Empleador')
            hoja_patrono.write(49,1, responsable_id.name)
            hoja_patrono.write(50,0,'Documento Identificación Responsable')
            hoja_patrono.write(50,1, responsable_id.identification_id)
            hoja_patrono.write(51,0,'Nacionalidad Del Responsable')
            hoja_patrono.write(51,1, responsable_id.country_id.name)
            hoja_patrono.write(52,0,'Año Del Informe ')
            hoja_patrono.write(52,1,dict['anio'])

            hoja_empleado = libro.add_worksheet('Empleado')
            datos = libro.add_worksheet('Hoja2')

            hoja_empleado.write(0, 0, 'Numero de trabajadores')
            hoja_empleado.write(0, 1, 'Primer Nombre')
            hoja_empleado.write(0, 2, 'Segundo Nombre')
            hoja_empleado.write(0, 3, 'Primer Apellido')
            hoja_empleado.write(0, 4, 'Segundo Apellido')
            hoja_empleado.write(0, 5, 'Nacionalidad')
            hoja_empleado.write(0, 6, 'Estado Civil')
            hoja_empleado.write(0, 7, 'Documento Identificación')
            hoja_empleado.write(0, 8, 'Número de Documento')
            hoja_empleado.write(0, 9, 'Pais Origen')
            hoja_empleado.write(0, 10, 'Lugar Nacimiento')
            hoja_empleado.write(0, 11, 'Número de Identificación Tributaria NIT')
            hoja_empleado.write(0, 12, 'Número de Afiliación IGSS')
            hoja_empleado.write(0, 13, 'Sexo (M) O (F)')
            hoja_empleado.write(0, 14, 'Fecha Nacimiento')
            hoja_empleado.write(0, 15, 'Cantidad de Hijos')
            hoja_empleado.write(0, 16, 'A trabajado en el extranjero ')
            hoja_empleado.write(0, 17, 'Ocupación en el extranjero')
            hoja_empleado.write(0, 18, 'Pais')
            hoja_empleado.write(0, 19, 'Motivo de finalización de la relación laboral en el extranjero')
            hoja_empleado.write(0, 20, 'Nivel Academico')
            hoja_empleado.write(0, 21, 'Título o diploma obtenido')
            hoja_empleado.write(0, 22, 'Pueblo de pertenencia')
            hoja_empleado.write(0, 23, 'Idiomas que dominca')

            hoja_empleado.write(0, 24, 'Temporalidad del contrato')
            hoja_empleado.write(0, 25, 'Tipo Contrato')
            hoja_empleado.write(0, 26, 'Fecha Inicio Labores')
            hoja_empleado.write(0, 27, 'Fecha Reinicio-laboreso')
            hoja_empleado.write(0, 28, 'Fecha Retiro Labores')
            hoja_empleado.write(0, 29, 'Ocupación')
            hoja_empleado.write(0, 30, 'Jornada de Trabajo')
            hoja_empleado.write(0, 31, 'Dias Laborados en el Año')

            hoja_empleado.write(0, 32, 'Número de expediente del permiso de extranjero')
            hoja_empleado.write(0, 33, 'Salario Mensual Nominal')
            hoja_empleado.write(0, 34, 'Salario Anual Nominal')
            hoja_empleado.write(0, 35, 'Bonificación Decreto 78-89  (Q.250.00)')
            hoja_empleado.write(0, 36, 'Total Horas Extras Anuales')
            hoja_empleado.write(0, 37, 'Valor de Hora Extra')
            hoja_empleado.write(0, 38, 'Monto Aguinaldo Decreto 76-78')
            hoja_empleado.write(0, 39, 'Monto Bono 14  Decreto 42-92')
            hoja_empleado.write(0, 40, 'Retribución por Comisiones')
            hoja_empleado.write(0, 41, 'Viaticos')
            hoja_empleado.write(0, 42, 'Bonificaciones Adicionales')
            hoja_empleado.write(0, 43, 'Retribución por vacaciones')
            hoja_empleado.write(0, 44, 'Retribución por Indemnización (Articulo 82)')
            # hoja_empleado.write(0, 45, 'Nombre, Denominación  o Razón Social del Patrono')

            fila = 1
            empleado_numero = 1
            numero = 1
            for empleado in empleados:
                logging.warn(empleado)
                nombre_empleado = empleado.name.split( )
                if nombre.primer_nombre:
                    nominas_lista = []
                    contrato = self.env['hr.contract'].search([('employee_id', '=', empleado.id),('state','=','open')])
                    nomina_id = self.env['hr.payslip'].search([['employee_id', '=', empleado.id]])
                    dias_trabajados = 0
                    salario_anual_nominal = 0
                    bonificacion = 0
                    estado_civil = 0
                    horas_extras = 0
                    aguinaldo = 0
                    bono = 0
                    bonificaciones_adicionales = 0
                    valor_horas_extras = 0
                    retribucion_comisiones = 0
                    viaticos = 0
                    retribucion_vacaciones = 0
                    bonificacion_decreto = 0
                    indemnizacion = 0
                    for nomina in nomina_id:
                        nomina_anio = nomina.date_from.year
                        if w['anio'] == nomina_anio:
                            if nomina.input_line_ids:
                                for entrada in nomina.input_line_ids:
                                    for horas_entrada in nomina.company_id.numero_horas_extras_ids:
                                        if entrada.code == horas_entrada.code:
                                            valor_horas_extras += entrada.amount
                            for linea in nomina.worked_days_line_ids:
                                dias_trabajados += linea.number_of_days
                            for linea in nomina.line_ids:
                                if linea.salary_rule_id.id in nomina.company_id.salario_ids.ids:
                                    salario_anual_nominal += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.bonificacion_ids.ids:
                                    bonificacion += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.aguinaldo_ids.ids:
                                    aguinaldo += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.bono_ids.ids:
                                    bono += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.horas_extras_ids.ids:
                                    horas_extras += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.retribucion_comisiones_ids.ids:
                                    retribucion_comisiones += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.viaticos_ids.ids:
                                    viaticos += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.retribucion_vacaciones_ids.ids:
                                    retribucion_vacaciones += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.indemnizacion_ids.ids:
                                    indemnizacion += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.bonificaciones_adicionales_ids.ids:
                                    bonificaciones_adicionales += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.decreto_ids.ids:
                                    bonificacion_decreto += linea.total
                    if empleado.gender == 'male':
                        genero = 'H'
                    if empleado.gender == 'female':
                        genero = 'M'
                    if empleado.marital == 'single':
                        estado_civil = 1
                    if empleado.marital == 'married':
                        estado_civil = 2
                    if empleado.marital == 'widower':
                        estado_civil = 3
                    if empleado.marital == 'divorced':
                        estado_civil = 4
                    if empleado.marital == 'separado':
                        estado_civil = 5
                    if empleado.marital == 'unido':
                        estado_civil = 6
                    dias_trabajados_anual = self.dias_trabajados_anual(empleado,w['anio'])
                    hoja_empleado.write(fila, 0, empleado_numero)
                    hoja_empleado.write(fila, 1, empleado.primer_nombre if empleado.primer_nombre else '')
                    hoja_empleado.write(fila, 2, empleado.segundo_nombre if empleado.segundo_nombre else '')
                    hoja_empleado.write(fila, 3, empleado.primer_apellido if empleado.primer_apellido else '')
                    hoja_empleado.write(fila, 4, empleado.segundo_apellido if empleado.segundo_apellido else '')
                    hoja_empleado.write(fila, 5, empleado.country_id.name)
                    hoja_empleado.write(fila, 6, estado_civil)
                    hoja_empleado.write(fila, 7, empleado.documento_identificacion)
                    hoja_empleado.write(fila, 8, empleado.identification_id)
                    hoja_empleado.write(fila, 9, empleado.pais_origen.name)
                    hoja_empleado.write(fila, 10, empleado.place_of_birth)
                    hoja_empleado.write(fila, 11, empleado.nit)
                    hoja_empleado.write(fila, 12, empleado.igss)
                    hoja_empleado.write(fila, 13, genero)
                    hoja_empleado.write(fila, 14, empleado.birthday)
                    hoja_empleado.write(fila, 15, empleado.children)
                    hoja_empleado.write(fila, 16, empleado.trabajado_extranjero)
                    hoja_empleado.write(fila, 17, empleado.forma_trabajo_extranjero)
                    hoja_empleado.write(fila, 18, empleado.pais_trabajo_extranjero_id.name)
                    hoja_empleado.write(fila, 19, empleado.finalizacion_laboral_extranjero)
                    hoja_empleado.write(fila, 20, empleado.nivel_academico)
                    hoja_empleado.write(fila, 21, empleado.profesion)
                    hoja_empleado.write(fila, 22, empleado.pueblo_pertenencia)
                    hoja_empleado.write(fila, 23, empleado.idioma)
                    hoja_empleado.write(fila, 24, contrato.temporalidad_contrato)
                    hoja_empleado.write(fila, 25, contrato.structure_type_id.default_struct_id.name)
                    hoja_empleado.write(fila, 26, contrato.date_start)
                    hoja_empleado.write(fila, 27, contrato.fecha_reinicio_labores)
                    hoja_empleado.write(fila, 28, contrato.date_end)
                    hoja_empleado.write(fila, 29, contrato.job_id.name)
                    hoja_empleado.write(fila, 30, empleado.jornada_trabajo)
                    hoja_empleado.write(fila, 31, dias_trabajados_anual)
                    hoja_empleado.write(fila, 32, empleado.permiso_trabajo)
                    hoja_empleado.write(fila, 33, contrato.wage)
                    # hoja_empleado.write(fila, 34, salario_anual_nominal)
                    hoja_empleado.write(fila, 34, (contrato.wage + contrato.base_extra) * 12)
                    hoja_empleado.write(fila, 35, bonificacion_decreto)
                    hoja_empleado.write(fila, 36, horas_extras)
                    hoja_empleado.write(fila, 37, ((horas_extras / valor_horas_extras) if valor_horas_extras > 0 else horas_extras))
                    hoja_empleado.write(fila, 38, aguinaldo)
                    hoja_empleado.write(fila, 39, bono)
                    hoja_empleado.write(fila, 40, retribucion_comisiones)
                    hoja_empleado.write(fila, 41, viaticos)
                    hoja_empleado.write(fila, 42, bonificaciones_adicionales)
                    hoja_empleado.write(fila, 43, retribucion_vacaciones)
                    hoja_empleado.write(fila, 44, indemnizacion)
                    # hoja_empleado.write(fila, 45, datos_compania.company_registry)
                    empleado_numero +=1

                    fila += 1
                    numero += 1

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'informe_del_empleador.xls'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.informe_empleador',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
