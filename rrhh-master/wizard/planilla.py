# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import base64
import xlwt
import StringIO
import logging

class rrhh_planilla_wizard(osv.osv_memory):
    _name = 'rrhh.planilla.wizard'

    _columns = {
        'nomina_id': fields.many2one('hr.payslip.run', 'Nomina', required=True),
        'planilla_id': fields.many2one('rrhh.planilla', 'Planilla', required=True),
        'archivo': fields.binary('Archivo'),
    }

    def _default_nomina(self, cr, uid, context):
        if 'active_id' in context:
            return context['active_id']
        return False

    _defaults = {
        'nomina_id': _default_nomina,
    }

    def generar(self, cr, uid, ids, context=None):
        for w in self.browse(cr, uid, ids):
            libro = xlwt.Workbook()
            hoja = libro.add_sheet('reporte')

            xlwt.add_palette_colour("custom_colour", 0x21)
            libro.set_colour_RGB(0x21, 200, 200, 200)
            estilo = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')

            hoja.write(0, 0, 'Planilla', estilo)
            hoja.write(0, 1, w.nomina_id.name, estilo)
            hoja.write(0, 2, 'Periodo', estilo)
            hoja.write(0, 3, w.nomina_id.date_start, estilo)
            hoja.write(0, 4, w.nomina_id.date_end, estilo)

            linea = 2
            num = 1

            hoja.write(linea, 0, 'No', estilo)
            hoja.write(linea, 1, 'Cod. de empleado', estilo)
            hoja.write(linea, 2, 'Nombre de empleado', estilo)
            hoja.write(linea, 3, 'Fecha de ingreso', estilo)
            hoja.write(linea, 4, 'Puesto', estilo)
            hoja.write(linea, 5, 'Dias', estilo)

            totales = []
            columna = 6
            for c in w.planilla_id.columna_id:
                hoja.write(linea, columna, c.name, estilo)
                columna += 1
                totales.append(0)
            totales.append(0)

            hoja.write(linea, columna, 'Liquido a recibir', estilo)
            hoja.write(linea, columna+1, 'Banco a depositar', estilo)
            hoja.write(linea, columna+2, 'Cuenta a depositar', estilo)
            hoja.write(linea, columna+3, 'Observaciones', estilo)

            linea += 1
            for l in w.nomina_id.slip_ids:
                dias = 0
                total_salario = 0

                hoja.write(linea, 0, num)
                hoja.write(linea, 1, l.employee_id.otherid)
                hoja.write(linea, 2, l.employee_id.name)
                hoja.write(linea, 3, l.contract_id.date_start)
                hoja.write(linea, 4, l.employee_id.job_id.name)
                for d in l.worked_days_line_ids:
                    dias += d.number_of_days
                hoja.write(linea, 5, dias)

                columna = 6
                for c in w.planilla_id.columna_id:
                    reglas = [x.id for x in c.regla_id]
                    total_columna = 0
                    for r in l.line_ids:
                        if r.salary_rule_id.id in reglas:
                            total_columna += r.total
                    if c.sumar:
                        total_salario += total_columna
                    totales[columna-6] += total_columna

                    hoja.write(linea, columna, total_columna)
                    columna += 1

                totales[columna-6] += total_salario
                hoja.write(linea, columna, total_salario)
                hoja.write(linea, columna+1, l.employee_id.bank_account_id.bank.name)
                hoja.write(linea, columna+2, l.employee_id.bank_account_id.acc_number)
                hoja.write(linea, columna+3, l.note)

                linea += 1
                num += 1

            columna = 6
            for t in totales:
                hoja.write(linea, columna, totales[columna-6], estilo)
                columna += 1

            f = StringIO.StringIO()
            libro.save(f)
            datos = base64.b64encode(f.getvalue())
            self.write(cr, uid, ids, {'archivo':datos})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.planilla.wizard',
            'res_id': ids[0],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
