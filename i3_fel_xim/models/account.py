# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime
import base64
import requests
import json
import logging
from decimal import Decimal, getcontext
import tempfile
from odoo.tools import config

_logger = logging.getLogger(__name__)

class CertificadorConfig(models.Model):
    _name = 'certificador.config'
    _description = 'Configuración del Certificador FEL'

    name = fields.Char('Nombre del Certificador', required=True)
    url_login = fields.Char('URL de Login', required=True)
    url_solicitud = fields.Char('URL de Solicitud', required=True)
    url_anulacion = fields.Char('URL de Anulación', required=True)
    usuario = fields.Char('Usuario', required=True)
    clave = fields.Char('Clave', required=True)
    es_pruebas = fields.Boolean('Modo Pruebas', default=True)
    token = fields.Char('Token', readonly=True)
    token_valido_hasta = fields.Datetime('Token Válido Hasta', readonly=True)

    def obtener_token(self):
        """Obtiene un token de autenticación del certificador."""
        try:
            payload = {
                'email': self.usuario,
                'password': self.clave,
                'device': 'Odoo'
            }
            response = requests.post(self.url_login, data=payload)
            response.raise_for_status()
            response_json = response.json()
            token = response_json.get("datos", {}).get("token")
            if not token:
                raise UserError("No se pudo obtener el token del certificador.")
            
            # Actualizar el token y su fecha de expiración
            self.write({
                'token': token,
                'token_valido_hasta': datetime.now() + timedelta(hours=1)  # Ejemplo: Token válido por 1 hora
            })
            return token
        except Exception as e:
            _logger.error(f"Error al obtener token: {e}")
            raise UserError(f"Error al obtener token: {e}")

class AccountMove(models.Model):
    _inherit = "account.move"

    # Campos para FEL
    serie_fel = fields.Char('Serie FEL', copy=False)
    numero_dte_uuid = fields.Char('UUID FEL', copy=False)
    numero_dte_sat = fields.Char('Número FEL', copy=False)
    firma_fel = fields.Char('Firma FEL', copy=False)
    pdf_fel = fields.Binary('PDF FEL', copy=False)
    pdf_fel_name = fields.Char('Nombre del PDF', default='fel.pdf', size=100, copy=False)
    fh_emision_certificacion = fields.Char('Fecha de Certificación', copy=False)
    enlace_fel_pdf = fields.Char('Enlace PDF', copy=False)
    enlace_fel_xml = fields.Char('Enlace XML', copy=False)
    documento_xml_fel = fields.Binary('XML Enviado', copy=False)
    documento_xml_fel_name = fields.Char('Nombre XML Enviado', default='xml_solicitud.xml', size=100, copy=False)
    resultado_xml_fel = fields.Binary('XML Respuesta', copy=False)
    resultado_xml_fel_name = fields.Char('Nombre XML Respuesta', default='xml_respuesta.xml', size=100, copy=False)
    motivo_fel = fields.Char('Motivo FEL', copy=False)
    son_servicios = fields.Boolean('Es Servicio', default=False)
    correlativo_fact_empresa = fields.Char('Correlativo Interno', copy=False)

    def construir_correlativo_interno(self):
        """Genera un correlativo interno para la factura."""
        diario = self.journal_id
        if not diario.generar_corr_interno:
            return

        if not self.correlativo_fact_empresa:
            sequence_code = diario.sequence_id.code
            if not sequence_code:
                raise UserError("El diario no tiene una secuencia configurada.")
            self.correlativo_fact_empresa = self.env['ir.sequence'].next_by_code(sequence_code)

    def _post(self, soft=True):
        """Extiende el método _post para incluir la solicitud de DTE."""
        super(AccountMove, self)._post(soft)
        self.solicitud_dte()
        return True

    def solicitud_dte(self):
        """Envía la solicitud de DTE al certificador."""
        if not self.journal_id.generar_fel:
            return

        config_certificador = self.env['certificador.config'].search([], limit=1)
        if not config_certificador:
            raise UserError("No se ha configurado ningún certificador.")

        # Obtener el token
        token = config_certificador.obtener_token()

        # Construir el cuerpo de la solicitud
        detalles = []
        for linea in self.invoice_line_ids:
            detalles.append({
                "numero_linea": len(detalles) + 1,
                "bien_servicio": "S" if linea.product_id.type == 'service' else "B",
                "cantidad": linea.quantity,
                "unidad_medida": "UND",
                "descripcion": linea.name,
                "precio_unitario": linea.price_unit,
                "precio": linea.price_subtotal,
                "descuento": linea.discount,
                "impuesto": "IVA",
                "monto_gravable": linea.price_subtotal,
                "monto_impuesto": linea.price_tax,
                "total": linea.price_total
            })

        cuerpo_solicitud = {
            "usuario_app": f"{self.env.company.name}/{self.invoice_user_id.name}",
            "es_pruebas": config_certificador.es_pruebas,
            "identificador_factura": self.name,
            "nit_emisor": self.company_id.vat,
            "fh_emision": str(self.invoice_date),
            "moneda": self.currency_id.name,
            "tipo_dte": self.journal_id.tipo_dte,
            "codigo_establecimiento": self.journal_id.codigo_establecimiento,
            "nit_receptor": self.partner_id.vat,
            "nombre_receptor": self.partner_id.name,
            "correo_receptor": self.partner_id.email or "",
            "direccion_receptor": self.partner_id.street or "",
            "codigo_postal_receptor": self.partner_id.zip or "",
            "municipio_receptor": self.partner_id.city or "",
            "departamento_receptor": self.partner_id.state_id.name or "",
            "pais_receptor": self.partner_id.country_id.code or "",
            "total_impuesto": self.amount_tax,
            "total_sin_impuesto": self.amount_untaxed,
            "total_factura": self.amount_total,
            "detalle": detalles
        }

        # Enviar la solicitud
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {token}"
        }
        response = requests.post(config_certificador.url_solicitud, headers=headers, data=json.dumps(cuerpo_solicitud))
        response_json = response.json()

        if response.status_code == 200 and response_json.get("exito"):
            datos = response_json.get("datos", {})
            self.write({
                'serie_fel': datos.get("serie"),
                'numero_dte_uuid': datos.get("uuid"),
                'numero_dte_sat': datos.get("numero"),
                'enlace_fel_pdf': datos.get("pdf_url"),
                'enlace_fel_xml': datos.get("xml_url"),
                'fh_emision_certificacion': datos.get("fecha_certificacion")
            })
            self.captura_pdf_fel(datos.get("pdf_base64"))
            self.captura_xml_fel(datos.get("xml_base64"))
        else:
            raise UserError(f"Error al enviar la solicitud: {response_json.get('mensaje')}")

    def captura_pdf_fel(self, pdf_base64):
        """Guarda el PDF generado por el certificador."""
        if pdf_base64:
            nombre_pdf = f"FEL-{self.numero_dte_uuid}.pdf"
            self.write({
                'pdf_fel': pdf_base64,
                'pdf_fel_name': nombre_pdf
            })

    def captura_xml_fel(self, xml_base64):
        """Guarda el XML generado por el certificador."""
        if xml_base64:
            nombre_xml = f"FEL-{self.numero_dte_uuid}.xml"
            self.write({
                'resultado_xml_fel': xml_base64,
                'resultado_xml_fel_name': nombre_xml
            })

    def anular_dte(self):
        """Anula un DTE ya emitido."""
        config_certificador = self.env['certificador.config'].search([], limit=1)
        if not config_certificador:
            raise UserError("No se ha configurado ningún certificador.")

        token = config_certificador.obtener_token()
        cuerpo_anulacion = {
            "motivo_anulacion": self.motivo_fel,
            "uuid": self.numero_dte_uuid,
            "usuario_app": f"{self.env.company.name}/{self.invoice_user_id.name}"
        }

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {token}"
        }
        response = requests.post(config_certificador.url_anulacion, headers=headers, data=json.dumps(cuerpo_anulacion))
        response_json = response.json()

        if response.status_code == 200 and response_json.get("exito"):
            self.write({'state': 'cancel'})
        else:
            raise UserError(f"Error al anular el DTE: {response_json.get('mensaje')}")