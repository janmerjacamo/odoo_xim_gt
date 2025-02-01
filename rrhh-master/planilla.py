# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
from datetime import datetime,timedelta
import calendar
import logging

class hr_employee(osv.osv):
    _inherit = 'hr.employee'

    _columns = {
        'job_id': fields.many2one('hr.job', 'Job Title', track_visibility='onchange'),
        'department_id': fields.many2one('hr.department', 'Department', track_visibility='onchange'),
        'diario_pago_id':fields.many2one('account.journal', 'Diario de Pago'),
        'igss': fields.char('IGSS'),
        'irtra': fields.char('IRTRA'),
        'nit': fields.char('NIT'),
        'recibo_id':fields.many2one('rrhh.recibo', 'Formato de recibo'),
        'nivel_academico': fields.char('Nivel Academico'),
        'profesion': fields.char('Profesion'),
        'etnia': fields.char('Etnia'),
        'idioma': fields.char('Idioma'),
        'pais_origen': fields.many2one('res.country','Pais Origen'),
        'trabajado_extranjero': fields.boolean('A trabajado en el extranjero'),
        'motivo_finalizacion': fields.char('Motivo de finalizacion'),
        'jornada_trabajo': fields.char('Jornada de Trabajo'),
        'permiso_trabajo': fields.char('Permiso de Trabajo'),
        'contacto_emergencia': fields.many2one('res.partner','Contacto de Emergencia'),
    }

class rrhh_planilla(osv.osv):
    _name = 'rrhh.planilla'

    _columns = {
        'name': fields.char('Nombre', size=40, required=True),
        'descripcion': fields.char('Descripción', size=120),
        'columna_id': fields.one2many('rrhh.planilla.columna', 'planilla_id', 'Columnas'),
    }

class rrhh_planilla_columna(osv.osv):
    _name = 'rrhh.planilla.columna'
    _order = 'sequence, name'

    _columns = {
        'name': fields.char('Nombre', size=40, required=True),
        'sequence': fields.integer('Secuencia', required=True, select=True),
        'regla_id': fields.many2many('hr.salary.rule', id1='columna_id', id2='regla_id', string='Reglas'),
        'planilla_id':fields.many2one('rrhh.planilla', 'Planilla', required=False),
        'sumar': fields.boolean('Sumar en liquido a recibir', help="Seleccionar si se desea que se tome en cuenta en la suma del liquido a recibir."),
    }
    _defaults = {
        'sequence': 5,
    }

class rrhh_recibo(osv.osv):
    _name = 'rrhh.recibo'

    _columns = {
        'name': fields.char('Nombre', size=40, required=True),
        'descripcion': fields.char('Descripción', size=120),
        'linea_id': fields.one2many('rrhh.recibo.linea', 'recibo_id', 'Lineas'),
        'linea_ingreso_id':fields.one2many('rrhh.recibo.linea', 'recibo_id', 'Ingresos', domain=[('tipo','=','ingreso')], context={'default_tipo':'ingreso'}),
        'linea_deduccion_id':fields.one2many('rrhh.recibo.linea', 'recibo_id', 'Deducciones', domain=[('tipo','=','deduccion')], context={'default_tipo':'deduccion'}),
    }

class rrhh_recibo_linea(osv.osv):
    _name = 'rrhh.recibo.linea'
    _order = 'sequence, name'

    _columns = {
        'name': fields.char('Nombre', size=40, required=True),
        'tipo':fields.selection([ ('ingreso','Ingreso'), ('deduccion','Deducción') ], 'Tipo'),
        'sequence': fields.integer('Secuencia', required=True, select=True),
        'regla_id': fields.many2many('hr.salary.rule', id1='linea_id', id2='regla_id', string='Reglas'),
        'recibo_id':fields.many2one('rrhh.recibo', 'Recibo', required=False),
    }
    _defaults = {
        'sequence': 5,
    }

class hr_contract(osv.osv):
    _inherit = 'hr.contract'

    _columns = {
        'base_extra': fields.float('Base Extra', digits=(16,2)),
    }

    def write(self, cr, uid, ids, values, context=None):
        if 'base_extra' in values or 'wage' in values:
            for record in self.browse(cr, uid, ids, context=context):
                message = "El contrato cambio, el salario paso de "+'{0:,.2f}'.format(record.wage)+" a "+'{0:,.2f}'.format(values.get('wage', record.wage))+ " y la base extra de "+'{0:,.2f}'.format(record.base_extra)+" a "+'{0:,.2f}'.format(values.get('base_extra', record.base_extra))
                self.pool.get('hr.employee').message_post(cr, uid, record.employee_id.id, body=message, context=context)

        return super(hr_contract, self).write(cr, uid, ids, values, context=context)

class hr_payslip_run(osv.osv):
    _inherit = 'hr.payslip.run'

    def draft_payslip_run(self, cr, uid, ids, context=None):
        for r in self.browse(cr, uid, ids, context=context):
            for s in r.slip_ids:
                self.pool.get('hr.payslip').cancel_sheet(cr, uid, [s.id], context=context)
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def close_payslip_run(self, cr, uid, ids, context=None):
        for r in self.browse(cr, uid, ids, context=context):
            for s in r.slip_ids:
                self.pool.get('hr.payslip').process_sheet(cr, uid, [s.id], context=context)

        return self.write(cr, uid, ids, {'state': 'close'}, context=context)

    def generar_pagos(self, cr, uid, ids, context=None):
        for r in self.browse(cr, uid, ids, context=context):
            for s in r.slip_ids:
                cuenta = s.journal_id.default_debit_account_id;
                lineas = [l for l in s.move_id.line_id if l.account_id.id == cuenta.id]

                total = 0
                for l in lineas:
                    total += l.credit - l.debit

                diario = s.employee_id.diario_pago_id
                if not diario:
                    raise osv.except_osv('Error', 'El empleado '+s.employee_id.name+' no tiene diario de pago')

                voucher_id = self.pool.get('account.voucher').create(cr, uid, {
                    'type': 'payment',
                    'journal_id': diario.id,
                    'account_id': diario.default_debit_account_id.id,
                    'amount': total,
                    'partner_id': s.employee_id.address_home_id.id,
                    'reference': r.name,
                    'company_id': s.company_id.id,
                    'tipo': 'no negociable',
                }, context=context)

                for l in lineas:
                    self.pool.get('account.voucher.line').create(cr, uid, {
                        'voucher_id': voucher_id,
                        'name': r.name,
                        'account_id': l.account_id.id,
                        'move_line_id': l.id,
                        'amount': l.credit - l.debit,
                        'type': 'dr',
                    }, context=context)

        return True

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'

    _columns = {
        'dia_del_mes': fields.integer('Dia del Mes'),
    }

    def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        res = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from=date_from, date_to=date_to, employee_id=employee_id, contract_id=contract_id, context=context)
        if date_to and date_to.split("-") > 2:
            res['value'].update({
                'dia_del_mes': int(date_to.split("-")[2])
            })
        return res

    def hr_verify_sheet(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'verify'}, context=context)

    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            if contract.date_start > date_from:
                date_from = contract.date_start
        res = super(hr_payslip, self).get_worked_day_lines(cr, uid, contract_ids, date_from, date_to, context)

        dias_totales_mes = {}
        horas_totales_mes = {}
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            dias = 0
            horas = 0
            day_from = datetime.strptime(date_from,"%Y-%m-%d")
            rango = calendar.monthrange(day_from.year, day_from.month)
            nb_of_days = (rango[1] - 1) + 1
            for day in range(0, nb_of_days):
                working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + timedelta(days=day), context)
                if working_hours_on_day:
                    dias += 1.0
                    horas += working_hours_on_day
            dias_totales_mes[contract.id] = dias
            horas_totales_mes[contract.id] = horas

        for r in res:
            r['dias_totales_mes'] = dias_totales_mes[r['contract_id']]

        return res

class hr_payslip_worked_days(osv.osv):
    _inherit = 'hr.payslip.worked_days'

    _columns = {
        'dias_totales_mes': fields.float('Dias totales'),
    }

class hr_payslip_employees(osv.osv_memory):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self, cr, uid, ids, context=None):
        emp_pool = self.pool.get('hr.employee')
        slip_pool = self.pool.get('hr.payslip')
        run_pool = self.pool.get('hr.payslip.run')
        slip_ids = []
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        run_data = {}
        if context and context.get('active_id', False):
            run_data = run_pool.read(cr, uid, [context['active_id']], ['date_start', 'date_end', 'credit_note'])[0]
        from_date =  run_data.get('date_start', False)
        to_date = run_data.get('date_end', False)
        credit_note = run_data.get('credit_note', False)
        if not data['employee_ids']:
            raise osv.except_osv(_("Warning!"), _("You must select employee(s) to generate payslip(s)."))
        for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
            slip_data = slip_pool.onchange_employee_id(cr, uid, [], from_date, to_date, emp.id, contract_id=False, context=context)
            res = {
                'employee_id': emp.id,
                'name': slip_data['value'].get('name', False),
                'struct_id': slip_data['value'].get('struct_id', False),
                'contract_id': slip_data['value'].get('contract_id', False),
                'payslip_run_id': context.get('active_id', False),
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': credit_note,
                'dia_del_mes': slip_data['value'].get('dia_del_mes', False),
            }
            slip_ids.append(slip_pool.create(cr, uid, res, context=context))
        slip_pool.compute_sheet(cr, uid, slip_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}
