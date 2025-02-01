from openerp.osv import fields, osv

class res_company(osv.osv):
    _inherit = "res.company"

    _columns = {
        'version_mensaje': fields.char('Version del mensaje'),
        'numero_patronal': fields.char('Numero patronal'),
        'tipo_planilla': fields.selection([('0', 'Produccion'),
                                           ('1', 'Pruebas')], 'Tipo de planilla'),
        'codigo_centro_trabajo': fields.char('Codigo del centro de trabajo'),
        'nombre_centro_trabajo': fields.char('Nombre del centro de trabajo'),
        'direccion_centro_trabajo': fields.char('Direccion del centro de trabajo'),
        'zona_centro_trabajo': fields.char('Zona donde se ubica el centro de trabajo'),
        'telefonos': fields.char('Telefonos (separados por guiones o diagonales)'),
        'fax': fields.char('Fax'),
        'nombre_contacto': fields.char('Nombre del contacto en centro de trabajo'),
        'correo_electronico': fields.char('correo_electronico'),
        'codigo_departamento': fields.char('Codigo departamento de la Republica'),
        'codigo_municipio': fields.char('Codigo municipio de la Republica'),
        'codigo_actividad_economica': fields.char('Codigo actividad economica'),
        'identificacion_tipo_planilla': fields.char('Identificacion de tipo de planilla'),
        'nombre_tipo_planilla': fields.char('Nombre del tipo de planilla'),
        'tipo_afiliados': fields.selection([('S', 'Sin IVS'),
                                            ('C', 'Con IVS')], 'Tipo de afiliados'),
        'periodo_planilla': fields.selection([('M', 'Mensual'),
                                              ('C', 'Catorcenal'),
                                              ('S', 'Semanal')], 'Periodo de planilla'),
        'departamento_republica': fields.char('Depto. de la Rep. donde laboran los empleados'),
        'actividad_economica': fields.char('Actividad economica'),
        'clase_planilla': fields.selection([('N', 'Normal'),
                                            ('V', 'Sin movimiento')], 'Clase de planilla'),
    }
