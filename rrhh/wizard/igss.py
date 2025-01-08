# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import base64
import xlwt
import StringIO
import logging
import datetime

class rrhh_igss_wizard(osv.osv_memory):
    _name = 'rrhh.igss.wizard'

    _columns = {
        'payslip_run_id': fields.many2one('hr.payslip.run', 'Payslip run'),
        'archivo': fields.binary('Archivo'),
    }

    def _default_payslip_run(self, cr, uid, context):
        if 'active_id' in context:
            return context['active_id']
        return False

    _defaults = {
        'payslip_run_id': _default_payslip_run,
    }

    def generar(self, cr, uid, ids, context=None):
        datos = ''
        for w in self.browse(cr, uid, ids):
            datos += str(w.payslip_run_id.slip_ids[0].company_id.version_mensaje) + '|' + str(datetime.date.today().strftime('%d/%m/%Y')) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.numero_patronal) + '|' + str(datetime.datetime.strptime(w.payslip_run_id.date_start,'%Y-%m-%d').date().strftime('%m')).lstrip('0') + '|' + str(datetime.datetime.strptime(w.payslip_run_id.date_start,'%Y-%m-%d').date().strftime('%Y')).lstrip('0') + '|' + str(w.payslip_run_id.slip_ids[0].company_id.name) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.vat) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.email) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.tipo_planilla) + '\r\n'
            datos += '[centros]' + '\r\n'
            datos += str(w.payslip_run_id.slip_ids[0].company_id.codigo_centro_trabajo) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.nombre_centro_trabajo) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.direccion_centro_trabajo) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.zona_centro_trabajo) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.telefonos) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.fax) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.nombre_contacto) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.correo_electronico) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.codigo_departamento) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.codigo_municipio) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.codigo_actividad_economica) + '\r\n'
            datos += '[tipos de planillas]' + '\r\n'
            datos += str(w.payslip_run_id.slip_ids[0].company_id.identificacion_tipo_planilla) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.nombre_tipo_planilla) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.tipo_afiliados) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.periodo_planilla) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.departamento_republica) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.actividad_economica) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.clase_planilla) + '\r\n'
            datos += '[liquidaciones]' + '\r\n'
            datos += '[empleados]' + '\r\n'
            for slip in w.payslip_run_id.slip_ids:
                contrato_ids = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', slip.employee_id.id)],offset=0,limit=1,order='date_start desc')
                datos += str(slip.employee_id.numero_liquidacion) + '|' + str(slip.employee_id.igss) + '|' + str(slip.employee_id.name) + '|'
                if contrato_ids:
                    contrato = self.pool.get('hr.contract').browse(cr, uid, contrato_ids)[0]
                    datos += str(contrato.wage) + '|' + str(datetime.datetime.strptime(contrato.date_start,'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|' + str(datetime.datetime.strptime(contrato.date_end,'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|'
                else:
                    datos += '|' + '|' + '|'
                datos += str(slip.employee_id.codigo_centro_trabajo) + '|' + str(slip.employee_id.nit) + '|' + str(slip.employee_id.codigo_ocupacion) + '|' + str(slip.employee_id.condicion_laboral) + '|' + '\r\n'
            datos += '[suspendidos]' + '\r\n'
            datos += '[licencias]' + '\r\n'
            datos += 'BAJO MI EXCLUSIVA Y ABSOLUTA RESPONSABILIDAD, DECLARO QUE LA INFORMACION QUE AQUI CONSIGNO ES FIEL Y EXACTA, QUE ESTA PLANILLA INCLUYE A TODOS LOS TRABAJADORES QUE ESTUVIERON A MI SERVICIO Y QUE SUS SALARIOS SON LOS EFECTIVAMENTE DEVENGADOS, DURANTE EL MES ARRIBA INDICADO' + '\r\n'
            datos += '[finplanilla]' + '\r\n'
            datos = datos.replace('False', '')
        datos = base64.b64encode(datos.encode("utf-8"))
        self.pool.get('rrhh.igss.wizard').write(cr, uid, ids[0], {'archivo':datos})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.igss.wizard',
            'res_id': ids[0],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
