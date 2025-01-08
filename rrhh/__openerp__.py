# -*- encoding: utf-8 -*-

#
# Status 1.0 - tested on Open ERP 8
#

{
    'name': 'rrhh',
    'version': '1.0',
    'category': 'Custom',
    'description': """
Módulo para generación de planilla
""",
    'author': 'Rodrigo Fernandez',
    'website': 'http://solucionesprisma.com/',
    'depends': ['hr_payroll'],
    'data': [
        'planilla.xml',
        'reports.xml',
        'hr_contract.xml',
        'res_company.xml',
        'hr.xml',
        'wizard/planilla.xml',
        'wizard/igss.xml',
        'wizard/finiquito.xml',
        'views/recibo.xml',
        'views/report_libro_salarios2.xml',
        'views/rrhh_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
