# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _



#Configurar en account.journal si requiere de certificación y reglas del juego
class AccountJournal(models.Model):
    _inherit = "account.journal"

    generar_fel = fields.Boolean('Generar FEL')
    generar_corr_interno = fields.Boolean('Corre. Interno FEL')
    contingencia_fel = fields.Boolean('Habilitar contingencia FEL')
    tipo_dte = fields.Selection([('FACT', 'Factura'), ('FCAM', 'Factura cambiaria'), ('FPEQ', 'Factura pequeño contribuyente'), ('FCAP', 'Factura Cambiaria Pequeño Contribuyente'), ('FESP', 'Factura Especial'), ('NABN', 'Nota de Abono'), ('RDON', 'Recibo por Donación'), ('RECI', 'Recibo'), ('NDEB', 'Nota de Débito'), ('NCRE', 'Nota de Crédito'),('FEXP', 'Exportación')], 'Tipo de DTE para Régimen FEL', copy=False)
    error_en_historial_fel = fields.Boolean('Registrar error FEL', help='Los errores no se muestran en pantalla, solo se registran en el historial')
    codigo_unidad_gravable = fields.Integer(string="Codigo Unidad Gravable", default=1, help="Este Datos es Obligatorio Para Fel, revisar la documentacion")
    
    direccion = fields.Many2one('res.company', string='Dirección Compañia FEL')
    codigo_establecimiento = fields.Integer(string='Código de establecimiento', default=1)
    

