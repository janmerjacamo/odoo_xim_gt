#-*- coding:utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import datetime

from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

from openerp.tools.safe_eval import safe_eval as eval
import logging

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'

    def process_sheet(self, cr, uid, ids, context=None):
        res = super(hr_payslip, self).process_sheet( cr, uid, ids, context=None)
        move_pool = self.pool.get('account.move')
        for slip in self.browse(cr, uid, ids, context=context):
            if slip.move_id:
                move_pool.button_cancel(cr, uid, [slip.move_id.id], context=context)
                for line in slip.move_id.line_id:
                    line.analytic_account_id = slip.contract_id.analytic_account_id.id
                move_pool.post(cr, uid, [slip.move_id.id], context=context)
        return res

    def compute_sheet(self, cr, uid, ids, context=None):
        res = super(hr_payslip, self).compute_sheet( cr, uid, ids, context=None)
        for nomina in self.browse(cr, uid, ids, context=context):
            mes_nomina = int(datetime.datetime.strptime(nomina.date_from, '%Y-%m-%d').date().strftime('%m'))
            anio_nomina = int(datetime.datetime.strptime(nomina.date_from, '%Y-%m-%d').date().strftime('%Y'))
            dia_nomina = int(datetime.datetime.strptime(nomina.date_to, '%Y-%m-%d').date().strftime('%d'))
            if dia_nomina > 20:
                for entrada in nomina.input_line_ids:
                    prestamo = self.pool.get('rrhh.prestamo').search(cr, uid, [('employee_id', '=', nomina.employee_id.id),('codigo','=',entrada.code)])
                    if prestamo:
                        for p in prestamo:
                            prestamo_browse = self.pool.get('rrhh.prestamo').browse(cr,uid,p)
                            prestamo_browse = prestamo_browse[0]
                            anio_prestamo = int(datetime.datetime.strptime(prestamo_browse[0].fecha_inicio, '%Y-%m-%d').date().strftime('%Y'))
                            if (prestamo_browse.codigo == entrada.code) and ((prestamo_browse.estado == 'nuevo') or (prestamo_browse.estado == 'proceso')):
                                for lineas in prestamo_browse.prestamo_ids:
                                    if (lineas.mes == mes_nomina) and (lineas.anio == anio_nomina):
                                        entrada.amount = lineas.monto
                                        lineas.nomina_id = nomina.id
                                cantidad_pagos = prestamo_browse.numero_descuentos
                                cantidad_pagados = 0
                                for lineas in prestamo_browse.prestamo_ids:
                                    if lineas.nomina_id:
                                        cantidad_pagados += 1
                                if cantidad_pagados > 0 and cantidad_pagados < cantidad_pagos:
                                    prestamo_browse.estado = "proceso"
                                if cantidad_pagados == cantidad_pagos and cantidad_pagos > 0:
                                    prestamo_browse.estado = "pagado"
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
