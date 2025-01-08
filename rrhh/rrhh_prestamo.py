# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp import api
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime, timedelta
import datetime
from dateutil.relativedelta import *
import calendar
import logging

class rrhh_prestamo(osv.osv):
    _name = 'rrhh.prestamo'
    _rec_name = 'descripcion'

    _columns = {
        'employee_id': fields.many2one('hr.employee','Empleado'),
        'fecha_inicio': fields.date('Fecha inicio'),
        'numero_descuentos': fields.integer('Numero de descuentos'),
        'total': fields.float('Total'),
        'mensualidad': fields.float('Mensualidad'),
        'prestamo_ids': fields.one2many('rrhh.prestamo.linea','prestamo_id',string='Lineas de prestamo'),
        'descripcion': fields.char(string='Descripción',required=True),
        'codigo': fields.char(string='Código',required=True),
        'estado': fields.selection([
            ('nuevo', 'Nuevo'),
            ('proceso','Proceso'),
            ('pagado', 'Pagado')
        ], string='Status', help='Estado del prestamo',readonly=True, default='nuevo'),
    }

    @api.one
    def generar_mensualidades(self):
        mes_inicial = datetime.datetime.strptime(self.fecha_inicio, '%Y-%m-%d').date()
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
                            self.env['rrhh.prestamo.linea'].create({'prestamo_id': self.id,'mes': mes,'anio': anio,'monto': self.mensualidad})
                        else:
                            pago_restante = self.total - total_sumado
                            ultimos_pagos_mensuales = pago_restante / diferencias_meses
                            self.env['rrhh.prestamo.linea'].create({'prestamo_id': self.id,'mes': mes,'anio': anio,'monto': pago_restante})
                        contador += 1
                else:
                    while contador < (self.numero_descuentos):
                        mes = mes_inicial + relativedelta(months=contador)
                        anio = mes.strftime('%Y')
                        mes = int(mes.strftime('%m'))
                        if contador <= (int(numero_pagos_mensualidad) -1 ):
                            self.env['rrhh.prestamo.linea'].create({'prestamo_id': self.id,'mes': mes,'anio': anio,'monto': self.mensualidad})
                        else:
                            pago_restante = self.total%self.mensualidad
                            ultimos_pagos_mensuales = pago_restante / diferencias_meses
                            logging.warn(ultimos_pagos_mensuales)
                            self.env['rrhh.prestamo.linea'].create({'prestamo_id': self.id,'mes': mes,'anio': anio,'monto': ultimos_pagos_mensuales})
                        contador += 1
        return True

    @api.one
    def prestamos(self):
        if self.prestamo_ids:
            cantidad_nominas = 0
            for nomina in self.prestamo_ids:
                if nomina.nomina_id:
                    cantidad_nominas += 1
            if cantidad_nominas == 0:
                self.prestamo_ids.unlink(cr, uid, ids, context)
                self.generar_mensualidades()
            else:
                raise osv.except_osv(_('Warning!'),_('No puede volver a generar mensualidades, por que ya existen nominas asociadas a este prestamo.'))
        else:
            self.generar_mensualidades()
        return True

    def unlink(self, cr, uid, ids, context=None):
        for prestamo in self.browse(cr, uid, ids, context=context):
            if prestamo.estado not in  ['draft']:
                raise osv.except_osv(_('Warning!'),_('No puede eliminar prestamo, por que ya existen nominas asociadas'))
        return super(rrhh_prestamo, self).unlink(cr, uid, ids, context)

class rrhh_prestamo_linea(osv.osv):
    _name = 'rrhh.prestamo.linea'

    _columns = {
        'mes': fields.selection([
            (1, 'Enero'),
            (2, 'Febrero'),
            (3, 'Marzo'),
            (4, 'Abril'),
            (5, 'Mayo'),
            (6, 'Junio'),
            (7, 'Julio'),
            (8, 'Agosto'),
            (9, 'Septiembre'),
            (10, 'Octubre'),
            (11, 'Noviembre'),
            (12, 'Diciembre'),
            ], string='Mes'),
        'monto': fields.float('Monto'),
        'anio': fields.integer('Año'),
        'nomina_id': fields.many2one('hr.payslip','Nomina'),
        'prestamo_id': fields.many2one('rrhh.prestamo','Prestamo'),
    }
