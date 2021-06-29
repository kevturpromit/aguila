# -*- coding: utf-8 -*-

from odoo import models, fields, api


class res_company(models.Model):
    _inherit = 'res.company'

    version_mensaje = fields.Char('Version del mensaje')
    numero_patronal = fields.Char('Numero patronal')
    tipo_planilla = fields.Selection([('0', 'Produccion'),
                                       ('1', 'Pruebas')], 'Tipo de planilla')
    codigo_centro_trabajo = fields.Char('Codigo del centro de trabajo')
    nombre_centro_trabajo = fields.Char('Nombre del centro de trabajo')
    direccion_centro_trabajo = fields.Char('Direccion del centro de trabajo')
    zona_centro_trabajo = fields.Char('Zona donde se ubica el centro de trabajo')
    telefonos = fields.Char('Telefonos (separados por guiones o diagonales)')
    fax = fields.Char('Fax')
    nombre_contacto = fields.Char('Nombre del contacto en centro de trabajo')
    correo_electronico = fields.Char('correo_electronico')
    codigo_departamento = fields.Char('Codigo departamento de la Republica')
    codigo_municipio = fields.Char('Codigo municipio de la Republica')
    codigo_actividad_economica = fields.Char('Codigo actividad economica')
    identificacion_tipo_planilla = fields.Char('Identificacion de tipo de planilla')
    nombre_tipo_planilla = fields.Char('Nombre del tipo de planilla')
    tipo_afiliados = fields.Selection([('S', 'Sin IVS'),
                                        ('C', 'Con IVS')], 'Tipo de afiliados')
    periodo_planilla = fields.Selection([('M', 'Mensual'),
                                          ('C', 'Catorcenal'),
                                          ('S', 'Semanal')], 'Periodo de planilla')
    departamento_republica = fields.Char('Depto. de la Rep. donde laboran los empleados')
    actividad_economica = fields.Char('Actividad economica')
    clase_planilla = fields.Selection([('N', 'Normal'),
                                        ('V', 'Sin movimiento')], 'Clase de planilla')
    representante_legal_id = fields.Many2one('hr.employee','Representante legal')
    ordinarias_ids = fields.Many2many('hr.salary.rule','rrhh_ordinarias_rel',string='Ordinarias')
    extras_ordinarias_ids = fields.Many2many('hr.salary.rule','rrhh_extra_ordinarias_rel',string='Extras ordinarias')
    ordinario_ids = fields.Many2many('hr.salary.rule','rrhh_ordinario_rel',string='Ordinario')
    extra_ordinario_ids = fields.Many2many('hr.salary.rule','rrhh_extra_ordinario_rel',string='Extra ordinario')
    igss_ids = fields.Many2many('hr.salary.rule','rrhh_igss_rel',string='IGGS')
    isr_ids = fields.Many2many('hr.salary.rule','rrhh_isr_rel',string='ISR')
    anticipos_ids = fields.Many2many('hr.salary.rule','rrhh_anticipos_rel',string='Anticipos')
    bonificacion_ids = fields.Many2many('hr.salary.rule','rrhh_bonificacion_rel',string='Bonificacion incentivo')
    bono_ids = fields.Many2many('hr.salary.rule','bono_company_rel',string='Bono 14')
    aguinaldo_ids = fields.Many2many('hr.salary.rule','rrhh_aguinaldo_rel',string='Aguinaldo')
    indemnizacion_ids= fields.Many2many('hr.salary.rule','rrhh_indemnizacion_rel',string='Retribución por Indemnización')
    salario_ids = fields.Many2many('hr.salary.rule','rrhh_salario_rel',string='Salario')
    origen_compania = fields.Selection([('nacional', 'Nacional'),
                                    ('extranjero', 'Extranjero')], 'Nacional o Extranjero')
    barrio_colonia = fields.Char('Barrio o Colonia')
    nomenclatura = fields.Char('Nomenclatura')
    sindicato = fields.Selection([('si', 'Si'),
                                    ('no', 'No')], 'Existe sindicato')
    contratar_personal = fields.Selection([('si', 'Si'),
                                    ('no', 'No')], 'Contratar nuevo personal')
    contabilidad_completa = fields.Selection([('si', 'Si'),
                                    ('no', 'No')], 'Contabilidad completa')
    rango_ingresos = fields.Selection([('si', 'Si'),
                                    ('no', 'No')], 'Rango ingresos anual')
    jefe_recursos_humanos_id = fields.Many2one('hr.employee','Jefe de recursos humanos')
    horas_extras_ids = fields.Many2many('hr.salary.rule','rrhh_horas_extras_rel',string='Horas extras')
    retribucion_comisiones_ids = fields.Many2many('hr.salary.rule','rrhh_retribucion_comisiones_rel',string='Redistribucion de comisiones')
    viaticos_ids= fields.Many2many('hr.salary.rule',string='Viaticos')
    retribucion_vacaciones_ids = fields.Many2many('hr.salary.rule','rrhh_redistribucion_vacaiones_rel',string='Retribucion por vacaciones')
    bonificaciones_adicionales_ids = fields.Many2many('hr.salary.rule','rrhh_bonificaciones_adicionales_rel', string='Bonificaciones adicionales')
    marca = fields.Char('Marca')
    anio_inicio_operaciones = fields.Integer('Año inicio de operaciones')
    tamanio_empresa_ventas = fields.Char('Tamaño de de empresa por ventas anuales')
    tamanio_empresa_trabajadores = fields.Char('Tamaño de empresa según cantidad de Trabajadores')
    actividad_gran_grupo = fields.Char('Actividad gran grupo')
    sub_actividad_economica = fields.Char('Sub actividad económica')
    ocupacion_grupo = fields.Char('Ocupación grupo')
    extras_ids = fields.Many2many('hr.salary.rule','rrhh_extras_rel',string='Extras')
    descuentos_ids = fields.Many2many('hr.salary.rule','rrhh_descuentos_rel',string='Descuentos')
    septimos_asuetos_ids = fields.Many2many('hr.salary.rule','rrhh_septimos_asuetos_rel', string="Septimos y asuetos")
    vacaciones_ids = fields.Many2many('hr.salary.rule','rrhh_vacaiones_rel', string="Vacaciones")
    decreto_ids = fields.Many2many('hr.salary.rule','rrhh_decretro_rel', string="Decreto")
    fija_ids = fields.Many2many('hr.salary.rule','rrhh_fija_rel', string="Fija")
    variable_ids = fields.Many2many('hr.salary.rule','rrhh_variable_rel', string="Variable")
    salario_promedio_ids = fields.Many2many('hr.salary.rule','rrhh_salario_promedio_rel', string="Salario promedio")
    numero_horas_extras_ids = fields.Many2many('hr.payslip.input.type','rrhh_num_horas_extras_rel', string='Numero horas extras')
    centro_trabajo_ids = fields.One2many('res.company.centro_trabajo','company_id',string="Centros de trabajo")
    otro_salario_ids = fields.Many2many('hr.salary.rule','rrhh_otro_salario_rel',string='Otros salarios')
    boni_incentivo_decreto_ids = fields.Many2many('hr.salary.rule','rrhh_boni_incentivo_decreto_rel',string='Bonificacion incentivo decreto')
    devolucion_isr_otro_ids = fields.Many2many('hr.salary.rule','rrhh_dev_isr_otro_rel',string='Devolución ISR')

class res_company_centro_trabajo(models.Model):
    _name = 'res.company.centro_trabajo'
    _description = 'Centro de trabajo'
    _rec_name = 'nombre'

    company_id = fields.Many2one('res.company','Compañia')
    codigo = fields.Char('Código')
    nombre = fields.Char('Nombre')
    direccion = fields.Char('Dirección')
    zona = fields.Char('Zona')
    telefono = fields.Char('Teléfono')
    fax = fields.Char('Fax')
    nombre_contacto = fields.Char('Nombre contacto')
    correo_electronico = fields.Char('Correo electronico')
    codigo_departamento = fields.Char('Codigo departamento')
    codigo_municipio = fields.Char('Código municipio')
    codigo_actividad_economica = fields.Char('Codigo actividad economica')
