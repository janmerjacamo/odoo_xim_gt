
# -*- encoding: utf-8 -*-

from openerp.osv import osv
from openerp.tools.translate import _
from dateutil import relativedelta
import datetime
from dateutil import parser
import logging

class ReporteLibroSalarios(osv.AbstractModel):
    _name = 'report.rrhh.libro_salarios'

    numero = 0


    def encabezado(self, cr, uid, o):
        r = relativedelta.relativedelta(datetime.date.today(), parser.parse(o.birthday))

        if o.gender == 'male':
            sexo = 'Masculino'
        else:
            sexo = 'Femenino'

        contrato = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', o.id)], order='date_start desc', limit=1)
        
        logging.warn(contrato)
        fecha_inicio = '2017-01-01'
        fecha_fin = '2017-12-31'
        
        return {'nombre':o.name, 
                'edad': r.years, 
                'sexo': sexo, 
                'nacionalidad': o.country_id.name, 
                'ocupacion': o.job_id.name, 
                'igss': o.igss, 
                'dpi': o.identification_id, 
                'fecha_inicio': fecha_inicio, 
                'fecha_fin': fecha_fin
                }

    def _calcular_monto(self, cr, uid, slip_id, obj):
        condicion = [('slip_id', '=', slip_id)]
        for regla in obj:
            condicion.append(('code', '=', regla.code))

        total = 0
        if len(condicion) > 1:
            line_ids = self.pool.get('hr.payslip.line').search(cr, uid, condicion)
            for line in self.pool.get('hr.payslip.line').browse(cr, uid, line_ids):
                total += line.total

        return(total)


    def lineas(self, cr, uid, o):
        lineas = {}
        numero_orden = 0
        payslip_ids = self.pool.get('hr.payslip').search(cr, uid, [('employee_id', '=', o.id)],order='date_from')
        for slip in self.pool.get('hr.payslip').browse(cr, uid, payslip_ids):
            periodo = slip.date_from[0:7]

            if periodo not in lineas:
                numero_orden += 1
                lineas[periodo] = {}
                lineas[periodo]['numero_orden'] = numero_orden
                lineas[periodo]['periodo'] = periodo
                lineas[periodo]['salario'] = 0
                lineas[periodo]['dias_trabajados'] = 0
                lineas[periodo]['horas_ordinarias'] = 0
                lineas[periodo]['horas_extra_ordinarias'] = 0
                lineas[periodo]['salario_ordinario'] = 0
                lineas[periodo]['salario_extra_ordinario'] = 0
                lineas[periodo]['septimos_asuetos'] = 0
                lineas[periodo]['vacaciones'] = 0
                lineas[periodo]['salario_total'] = 0 
                lineas[periodo]['igss'] = 0
                lineas[periodo]['otras_deducciones_legales'] = 0
                lineas[periodo]['total_deducciones'] = 0
                lineas[periodo]['decreto_42_92'] = 0
                lineas[periodo]['bonificacion_incentivo'] = 0
                lineas[periodo]['liquido_recibir'] = 0

            dias_trabajados = 0
            for dias in slip.worked_days_line_ids:
                dias_trabajados += dias.number_of_days

            lineas[periodo]['salario'] += slip.contract_id.wage
            lineas[periodo]['dias_trabajados'] += dias_trabajados
            lineas[periodo]['horas_ordinarias'] += 0
            lineas[periodo]['horas_extra_ordinarias'] += 0
            lineas[periodo]['salario_ordinario'] += slip.contract_id.wage
            lineas[periodo]['salario_extra_ordinario'] += self._calcular_monto(cr, uid, slip.id, slip.contract_id.salario_extra_ordinario_id)
            lineas[periodo]['septimos_asuetos'] += self._calcular_monto(cr, uid, slip.id, slip.contract_id.septimos_asuetos_id)
            lineas[periodo]['vacaciones'] += self._calcular_monto(cr, uid, slip.id, slip.contract_id.vacaciones_id)
            lineas[periodo]['salario_total'] += slip.contract_id.wage + slip.contract_id.base_extra
            lineas[periodo]['igss'] += self._calcular_monto(cr, uid, slip.id, slip.contract_id.igss_id)
            lineas[periodo]['otras_deducciones_legales'] += self._calcular_monto(cr, uid, slip.id, slip.contract_id.otras_deducciones_legales_id)
            lineas[periodo]['total_deducciones'] += self._calcular_monto(cr, uid, slip.id, slip.contract_id.total_deducciones_id)
            lineas[periodo]['decreto_42_92'] += self._calcular_monto(cr, uid, slip.id, slip.contract_id.decreto_42_92_id)
            lineas[periodo]['bonificacion_incentivo'] += self._calcular_monto(cr, uid, slip.id, slip.contract_id.bonificacion_incentivo_id)
            lineas[periodo]['liquido_recibir'] += slip.contract_id.wage + self._calcular_monto(cr, uid, slip.id, slip.contract_id.liquido_recibir_id)

        res = []
        keylist = lineas.keys()
        keylist.sort()
        for i in keylist:
            res.append(lineas[i])

        return res

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        order_obj = self.pool['hr.employee']

        report = report_obj._get_report_from_name(cr, uid, 'rrhh.libro_salarios')
        empleado = order_obj.browse(cr, uid, ids, context=context)

        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'data': data,
            'docs': empleado,
            'encabezado': self.encabezado,
            'lineas': self.lineas,
            'cursor': cr,
            'uid': uid,
        }

        return report_obj.render(cr, uid, ids, 'rrhh.libro_salarios', docargs, context=context)

