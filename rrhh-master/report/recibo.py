# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv
from openerp.tools.translate import _
import logging

class ReportRecibo(osv.AbstractModel):
    _name = 'report.rrhh.recibo'

    def lineas(self, o):
        result = {'lineas': [], 'totales': [0, 0]}
        if o.employee_id.recibo_id:

            lineas_reglas = {}
            for l in o.line_ids:
                if l.salary_rule_id.id not in lineas_reglas:
                    lineas_reglas[l.salary_rule_id.id] = 0
                lineas_reglas[l.salary_rule_id.id] += l.total

            recibo = o.employee_id.recibo_id
            lineas_ingresos = []
            for li in recibo.linea_ingreso_id:
                datos = {'nombre': li.name, 'total': 0}
                for r in li.regla_id:
                    datos['total'] += lineas_reglas.get(r.id, 0)
                    result['totales'][0] += lineas_reglas.get(r.id, 0)
                lineas_ingresos.append(datos)

            lineas_deducciones = []
            for ld in recibo.linea_deduccion_id:
                datos = {'nombre': ld.name, 'total': 0}
                for r in ld.regla_id:
                    datos['total'] += lineas_reglas.get(r.id, 0)
                    result['totales'][1] += lineas_reglas.get(r.id, 0)
                lineas_deducciones.append(datos)

            largo = max(len(lineas_ingresos), len(lineas_deducciones))
            lineas_ingresos += [None] * (largo - len(lineas_ingresos))
            lineas_deducciones += [None] * (largo - len(lineas_deducciones))

            result['lineas'] = zip(lineas_ingresos, lineas_deducciones)

        return result

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        recibo_obj = self.pool['hr.payslip']

        report = report_obj._get_report_from_name(cr, uid, 'rrhh.recibo')
        recibos = recibo_obj.browse(cr, uid, ids, context=context)

        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': recibos,
            'lineas': self.lineas,
        }

        return report_obj.render(cr, uid, ids, 'rrhh.recibo', docargs, context=context)
