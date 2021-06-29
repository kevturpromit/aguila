# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, AccessError
import datetime
import logging
from dateutil.relativedelta import *
import calendar

class rrhh_prestamo(models.Model):
    _name = 'rrhh.prestamo'
    _description = 'Prestamo'
    _rec_name = 'descripcion'

    employee_id = fields.Many2one('hr.employee','Empleado')
    fecha_inicio = fields.Date('Fecha inicio')
    numero_descuentos = fields.Integer('Numero de descuentos')
    total = fields.Float('Total')
    mensualidad = fields.Float('Mensualidad')
    prestamo_ids = fields.One2many('rrhh.prestamo.linea','prestamo_id',string='Lineas de prestamo')
    descripcion = fields.Char(string='Descripción',required=True)
    codigo = fields.Char(string='Código',required=True)
    estado = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('proceso','Proceso'),
        ('pagado', 'Pagado')
    ], string='Status', help='Estado del prestamo',readonly=True, default='nuevo')
    pendiente_pagar_prestamo = fields.Float(compute='_compute_prestamo', string='Pendiente a pagar del prestamos', )

    def _compute_prestamo (self):
        for prestamo in self:
            total_prestamo = 0
            total_prestamo_pagado = 0
            nominas = 0
            for linea in prestamo.prestamo_ids:
                for nomina in linea.nomina_id:
                    nominas += 1
                    for nomina_entrada in nomina.input_line_ids:
                        if prestamo.codigo == nomina_entrada.code:
                            total_prestamo_pagado += nomina_entrada.amount
                total_prestamo += linea.monto
            prestamo.pendiente_pagar_prestamo = total_prestamo - total_prestamo_pagado
            if prestamo.pendiente_pagar_prestamo == 0 and nominas > 0:
                prestamo.estado = 'pagado'
            return True

    def generar_mensualidades(self):
        mes_inicial = self.fecha_inicio
        mes  = 0
        if self.mensualidad > 0 and self.numero_descuentos > 0:
            total = self.mensualidad * self.numero_descuentos
            if self.mensualidad <= self.total:
                numero_pagos_mensualidad = self.total / self.mensualidad
                mes_final_pagos_mensuales = mes_inicial + relativedelta(months=int(numero_pagos_mensualidad) -1)
                anio_final = mes_final_pagos_mensuales.strftime('%Y')
                diferencias_meses = self.numero_descuentos - int(numero_pagos_mensualidad)
                contador = 0
                if diferencias_meses < 0:
                    total_sumado = 0
                    diferencia = (diferencias_meses*-1) + self.numero_descuentos
                    while contador <= (self.numero_descuentos -1):
                        mes = mes_inicial + relativedelta(months=contador)
                        anio = mes.strftime('%Y')
                        mes = int(mes.strftime('%m'))
                        if contador < (self.numero_descuentos -1):
                            total_sumado += self.mensualidad
                            self.env['rrhh.prestamo.linea'].create({'prestamo_id': self.id,'mes': str(mes),'anio': anio,'monto': self.mensualidad})
                        else:
                            pago_restante = self.total - total_sumado
                            ultimos_pagos_mensuales = pago_restante / diferencias_meses
                            self.env['rrhh.prestamo.linea'].create({'prestamo_id': self.id,'mes': str(mes),'anio': anio,'monto': pago_restante})
                        contador += 1
                else:
                    while contador < (self.numero_descuentos):
                        mes = mes_inicial + relativedelta(months=contador)
                        anio = mes.strftime('%Y')
                        mes = int(mes.strftime('%m'))
                        if contador <= (int(numero_pagos_mensualidad) -1 ):
                            self.env['rrhh.prestamo.linea'].create({'prestamo_id': self.id,'mes': str(mes),'anio': anio,'monto': self.mensualidad})
                        else:
                            pago_restante = self.total%self.mensualidad
                            ultimos_pagos_mensuales = pago_restante / diferencias_meses
                            self.env['rrhh.prestamo.linea'].create({'prestamo_id': self.id,'mes': str(mes),'anio': anio,'monto': ultimos_pagos_mensuales})
                        contador += 1
        return True

    def prestamos(self):
        if self.prestamo_ids:
            cantidad_nominas = 0
            for nomina in self.prestamo_ids:
                if nomina.nomina_id:
                    cantidad_nominas += 1
            if cantidad_nominas == 0:
                self.prestamo_ids.unlink()
                self.generar_mensualidades()
            else:
                raise ValidationError(_('No puede volver a generar mensualidades, por que ya existen nominas asociadas a este prestamo.'))
        else:
            self.generar_mensualidades()
        return True
    
    def cancelar(self):
        for prestamo in self:
            prestamo.estado = 'proceso'
        return True

    def unlink(self):
        for prestamo in self:
            if not prestamo.estado == 'nuevo':
                raise UserError(_('No puede eliminar prestamo, por que ya existen nominas asociadas'))
        return super(hr_prestamo, self).unlink()

class rrhh_prestamo_linea(models.Model):
    _name = 'rrhh.prestamo.linea'
    _description = 'Prestamo linea'

    mes = fields.Selection([
        ('1', 'Enero'),
        ('2', 'Febrero'),
        ('3', 'Marzo'),
        ('4', 'Abril'),
        ('5', 'Mayo'),
        ('6', 'Junio'),
        ('7', 'Julio'),
        ('8', 'Agosto'),
        ('9', 'Septiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre'),
        ], string='Mes')
    monto = fields.Float('Monto')
    anio = fields.Integer('Año')
    nomina_id = fields.Many2many('hr.payslip','prestamo_nominda_id_rel',string='Nomina')
    prestamo_id = fields.Many2one('rrhh.prestamo','Prestamo')

