# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import base64
import xlwt
import StringIO
import logging
import time
from openerp.addons.l10n_gt_extra.a_letras import num_a_letras

class rrhh_finiquito_wizard(osv.osv_memory):
    _name = 'rrhh.finiquito.wizard'

    _columns = {
    'empleado_id': fields.many2one('hr.employee', 'Empleado', required=True),
    'ordinarios_id': fields.many2many('hr.salary.rule', 'ordinario_regla_rel', 'finiquito_id', 'regla_id', string='Reglas Salario Ordinario'),
    'extraordinarios_id': fields.many2many('hr.salary.rule', 'extraordinario_regla_rel', 'finiquito_id', 'regla_id', string='Reglas Salario Extraordinario'),
    'representante_legal': fields.char("Representante legal"),
    'numero_cheque': fields.char("Numero de cheque"),
    'banco_emisor': fields.char("Banco emisor"),
    'archivo': fields.binary('Archivo'),
    'fecha_inicio': fields.date('Fecha inicio', required=True),
    'fecha_fin': fields.date('Fecha fin', required=True),
    'otros_descuentos_id': fields.many2many('hr.salary.rule', 'otros_descuentos_regla_rel', 'finiquito_id', 'regla_id', string='Otros Descuentos'),
    'dias_vacaciones_totales': fields.integer('Dias de vacaciones totales'),
    'nomina_descuentos_id': fields.many2one('hr.payslip', 'Nomina de descuentos', required=True),
    }

    def _default_empleado(self, cr, uid, context):
        if 'active_id' in context:
            return context['active_id']
        return False

    _defaults = {
        'empleado_id': _default_empleado,
    }

    def generar(self, cr, uid, ids, context=None):
        for w in self.browse(cr, uid, ids):
            libro = xlwt.Workbook()
            hoja = libro.add_sheet('reporte')

            xlwt.add_palette_colour("custom_colour", 0x21)
            libro.set_colour_RGB(0x21, 200, 200, 200)
            estilo = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')

            contrato_ids = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', w.empleado_id.id)],offset=0,limit=1,order='date_start desc')
            contrato = self.pool.get('hr.contract').browse(cr, uid, contrato_ids)[0]

            hoja.write(2, 2, w.empleado_id.company_id.name)
            hoja.write(3, 2, 'FINIQUITO LABORAL POR RENUNCIA')
            hoja.write(5, 0, 'NOMBRE:')
            hoja.write(5, 2, w.empleado_id.name)
            hoja.write(5, 3, 'PUESTO:')
            hoja.write(5, 4, contrato.job_id.name)
            hoja.write(6, 0, 'FECHA INGRESO:')
            hoja.write(6, 2, contrato.date_start)
            hoja.write(6, 3, 'FECHA:')
            hoja.write(6, 4, time.strftime("%d/%m/%Y"))
            hoja.write(7, 0, 'FECHA EGRESO:')
            hoja.write(7, 2, contrato.date_end)

            hoja.write(10, 2, 'S A L A R I O S    D E V E N G A D O S')
            hoja.write(11, 0, 'No.')
            hoja.write(11, 1, 'MES')
            hoja.write(11, 3, 'SALARIO ORDINARIO')
            hoja.write(11, 4, 'SALARIO EXTRA-ORDI.')
            hoja.write(11, 5, 'SALARIO TOTAL')
            hoja.write(11, 6, 'DIAS TRABAJ.')

            nomina_ids = self.pool.get('hr.payslip').search(cr, uid, [('employee_id', '=', w.empleado_id.id), ('contract_id', '=', contrato.id), ('date_from', '>=', w.fecha_inicio), ('date_to', '<=', w.fecha_fin)])

            logging.warn(w.empleado_id.id)
            logging.warn(contrato.id)
            logging.warn(nomina_ids)

            # if len(nomina_ids) > 0:
                # nomina_final_id = nomina_ids.pop()
                # logging.warn(nomina_final_id)
            # else:
                # nomina_final_id = False

            logging.warn(nomina_ids)


            ordinarios_reglas_ids = [x.id for x in w.ordinarios_id]
            extraordinarios_reglas_ids = [x.id for x in w.extraordinarios_id]
            otros_descuentos_reglas_ids = [x.id for x in w.otros_descuentos_id]

            linea = 12
            numero = 1
            salario_ordinario = 0
            total_devengado_total = 0
            total_devengado_ordinario = 0
            total_devengado_extraordinario = 0
            total_otros_descuentos = 0
            total_dias_trabajados = 0
            for nomina in self.pool.get('hr.payslip').browse(cr, uid, nomina_ids):

                salario_total = 0
                salario_ordinario = 0
                salario_extraordinario = 0
                for nomina_line in nomina.line_ids:

                    if nomina_line.salary_rule_id.id in ordinarios_reglas_ids:
                        salario_ordinario += nomina_line.total
                        total_devengado_ordinario += nomina_line.total
                        salario_total += nomina_line.total
                        total_devengado_total += nomina_line.total

                    if nomina_line.salary_rule_id.id in extraordinarios_reglas_ids:
                        salario_extraordinario += nomina_line.total
                        total_devengado_extraordinario += nomina_line.total
                        salario_total += nomina_line.total
                        total_devengado_total += nomina_line.total

                    if nomina_line.salary_rule_id.id in otros_descuentos_reglas_ids:
                        total_otros_descuentos += nomina_line.total

                dias_trabajados = 0
                for nomina_dias in nomina.worked_days_line_ids:
                    dias_trabajados += nomina_dias.number_of_days
                    total_dias_trabajados += nomina_dias.number_of_days

                hoja.write(linea, 0, numero)
                hoja.write(linea, 1, nomina.date_from)
                hoja.write(linea, 3, salario_ordinario)
                hoja.write(linea, 4, salario_extraordinario)
                hoja.write(linea, 5, salario_total)
                hoja.write(linea, 6, dias_trabajados)
                numero += 1
                linea += 1

            linea += 1
            hoja.write(linea, 1, 'TOTAL DEVENGADO')
            hoja.write(linea, 3, total_devengado_ordinario)
            hoja.write(linea, 4, total_devengado_extraordinario)
            hoja.write(linea, 5, total_devengado_total)
            hoja.write(linea, 6, total_dias_trabajados)

            linea += 2
            hoja.write(linea, 4, 'SUELDO MENSUAL ACTUAL')
            hoja.write(linea, 6, salario_total)

            subtotal = 0
            if w.nomina_descuentos_id.id:
                linea += 2
                for nomina in self.pool.get('hr.payslip').browse(cr, uid, [w.nomina_descuentos_id.id]):
                    for nomina_line in nomina.line_ids:
                        hoja.write(linea, 1, nomina_line.salary_rule_id.code)
                        hoja.write(linea, 2, nomina.date_from)
                        hoja.write(linea, 3, 'AL')
                        hoja.write(linea, 4, nomina.date_to)
                        hoja.write(linea, 5, 'No. dias')
                        hoja.write(linea, 6, nomina_line.total)
                        subtotal += nomina_line.total
                        linea += 1

            linea += 1
            hoja.write(linea, 4, 'REALES')
            hoja.write(linea, 5, 'GOZADOS')
            linea += 1
            hoja.write(linea, 2, 'DIAS VACACIONES')
            hoja.write(linea, 4, w.dias_vacaciones_totales)
            hoja.write(linea, 5, w.dias_vacaciones_totales - w.empleado_id.remaining_leaves)
            linea += 2
            hoja.write(linea, 2, 'SUB-TOTAL')
            hoja.write(linea, 6, subtotal)
            linea += 2
            hoja.write(linea, 1, '(-) OTROS DESCUENTOS')
            hoja.write(linea, 6, total_otros_descuentos)
            linea += 1
            hoja.write(linea, 1, '(-) RETENCION LABORAL IGSS')
            linea += 1
            hoja.write(linea, 1, '(-) COOPERATIVA COCRECER')
            linea += 1
            hoja.write(linea, 1, '(-) DIADEMA TELEFONICA')
            linea += 1
            hoja.write(linea, 1, '(-) VIATICOS')
            linea += 1
            hoja.write(linea, 5, 'T O T A L')

            linea += 2
            hoja.write(linea, 0, "FIRMA DE RECIBIDO:")
            hoja.write(linea, 5, "DPI: " + w.empleado_id.identification_id)
            linea += 2
            hoja.write(linea, 0, "PAGO CON CHEQUE:")
            hoja.write(linea, 5, "BANCO:")
            linea += 2
            current_user = self.pool.get('res.users').browse(cr, uid, uid)
            hoja.write(linea, 0, "HECHO POR: " + current_user.name)
            hoja.write(linea, 5, "REVISADO POR:")

            linea += 2
            hoja.write(linea, 2, "FINIQUITO DE PRESTACIONES LABORALES:")
            linea += 2
            hoja.write(linea, 0, "YO " + w.representante_legal + " REPRESENTANTE LEGAL DE " + w.empleado_id.company_id.name + " POR MEDIO DEL PRESENTE MANIFIESTO QUE")
            linea += 1
            hoja.write(linea, 0, "CON FECHA 15 DE JULIO DE 2016, EL TRABAJADOR " + w.empleado_id.name + ", RENUNCIO AL TRABAJO QUE VENIA")
            linea += 1
            hoja.write(linea, 0, "DESEMPENANDO EN " + w.empleado_id.company_id.name + ", POR LO QUE A CONTINUACION SE PROCEDE AL FINIQUITO DE PRESTACIONES")
            linea += 1
            hoja.write(linea, 0, "LABORALES PENDIENTES DE PAGO HASTA LA FECHA.")
            linea += 2
            hoja.write(linea, 0, "YO: " + w.empleado_id.name + ", HABIENDO RECIBIDO A MI ENTERA CONFORMIDAD EL MONTO GLOBAL DE LAS")
            linea += 1
            hoja.write(linea, 0, "PRESTACIONES LABORALES DETALLADAS ANTERIORMENTE, Y QUE SUMAN LA CANTIDAD DE ")
            linea += 1
            hoja.write(linea, 0, num_a_letras(subtotal) + "(Q. " + str(subtotal) + "  MEDIANTE  EL CHEQUES No " + w.numero_cheque + " DEL ")
            linea += 1
            hoja.write(linea, 0, w.banco_emisor + ",  MISMOS QUE RECIBO EN ESTE MOMENTO. ME RESERVO RECLAMACION Y DEMANDA ALGUNA CONTRA LA")
            linea += 1
            hoja.write(linea, 0, "ENTIDAD  " + w.empleado_id.company_id.name + ", Y  A LA CUAL POR ESTE ACTO LE OTORGO MI MAS COMPLETO, TOTAL FINIQUITO LABORAL,")
            linea += 1
            hoja.write(linea, 0, "BAJO PACTO EXPRESO DE NO PEDIR EN FE EXPUESTO, RECTIFICO, ACEPTO Y FIRMO EL PRESENTE FINIQUITO, EN LA")
            linea += 1
            hoja.write(linea, 0, "CIUDAD DE GUATEMALA, EL 15 DE JULIO   DEL ANO DOS MIL DIESISES.")

            f = StringIO.StringIO()
            libro.save(f)
            datos = base64.b64encode(f.getvalue())
            self.write(cr, uid, ids, {'archivo':datos})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.finiquito.wizard',
            'res_id': ids[0],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
