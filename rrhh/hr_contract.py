from openerp.osv import fields, osv
from openerp.tools.translate import _


class hr_contract_type(osv.osv):
    _inherit = "hr.contract.type"

    _columns = {
        'calcula_indemnizacion': fields.boolean('Calcula indemnizacion'),
    }

class hr_contract(osv.osv):
    _inherit = "hr.contract"

    _columns = {
        'motivo_terminacion': fields.selection([
            ('reuncia', 'Renuncia'),
            ('despido', 'Despido'),
            ('despido_justificado', 'Despido Justificado'),
            ], 'Motivo de terminacion'),
        'salario_extra_ordinario_id': fields.many2many('hr.salary.rule', 'salario_extra_regla_rel', 'contrato_id', 'regla_id', string='Salario extra ordinario'),
        'igss_id': fields.many2many('hr.salary.rule', 'igss_regla_rel', 'contrato_id', 'regla_id', string='IGSS'),
        'otras_deducciones_legales_id': fields.many2many('hr.salary.rule', 'otras_deducciones_legales_regla_rel', 'contrato_id', 'regla_id', string='Otras deducciones legales'),
        'total_deducciones_id': fields.many2many('hr.salary.rule', 'total_deducciones_regla_rel', 'contrato_id', 'regla_id', string='Total deducciones'),
        'decreto_42_92_id': fields.many2many('hr.salary.rule', 'decreto_42_92_regla_rel', 'contrato_id', 'regla_id', string='Decreto 42-92'),
        'bonificacion_incentivo_id': fields.many2many('hr.salary.rule', 'bonificacion_incentivo_regla_rel', 'contrato_id', 'regla_id', string='Bonificacion Incentivo'),
        'comisiones_id': fields.many2many('hr.salary.rule', 'comisiones_regla_rel', 'contrato_id', 'regla_id', string='Comisiones'),
        'septimos_asuetos_id': fields.many2many('hr.salary.rule', 'septimos_asuetos_regla_rel', 'contrato_id', 'regla_id', string='Septimos asuetos'),
        'vacaciones_id': fields.many2many('hr.salary.rule', 'vacaciones_regla_rel', 'contrato_id', 'regla_id', string='Vacaciones'),
        'liquido_recibir_id': fields.many2many('hr.salary.rule', 'liquido_recibir_regla_rel', 'contrato_id', 'regla_id', string='Liquido a recibir'),
    }
