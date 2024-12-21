# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, ValidationError

from datetime import datetime
import base64
import requests
import json
import logging
from decimal import *
import base64, os, tempfile
import binascii 
from odoo.tools import config

    
class AccountMove(models.Model):
    _inherit = "account.move"

    #Referencias para ubicar FEL
    serie_fel = fields.Char('Serie FACT', copy=False)
    numero_dte_uuid = fields.Char('UUID FACT', copy=False)
    numero_dte_sat = fields.Char('Número FACT', copy=False)
    firma_fel = fields.Char('Firma FEL', copy=False)
    certificador_fel = fields.Char('Certificador FEL', copy=False)
    pdf_fel = fields.Binary('PDF FEL', copy=False)
    pdf_fel_name = fields.Char('Nombre del archivo PDF de la factura', default='fel.pdf', size=100, copy=False)    
    fh_emision_certificacion = fields.Char(string="Fecha FEL",copy=False)
    son_servicios = fields.Boolean(string="Switch a Servicios", default=False)
    correlativo_fact_empresa = fields.Char(string="Correlativo Interno", copy=False)
    enlace_fel_pdf = fields.Char(string="Enlace FEL", copy=False)
    enlace_fel_xml = fields.Char(string="Enlace XML",copy=False)
    son_servicios = fields.Boolean(string="Switch a Servicios", default=False)
    
    # XML utilizados para el FEL
    documento_xml_fel = fields.Binary('Documento xml enviado para FEL', copy=False)
    documento_xml_fel_name = fields.Char('Nombre doc xml  enviado apra FEL', default='xml_solicitud.xml', size=100, copy=False)
    resultado_xml_fel = fields.Binary('Resultado xml de certificacion FEL. xml_dte final', copy=False)
    resultado_xml_fel_name = fields.Char('Nombre del xml de certificacion FEL', default='xml_respuesta.xml', size=100, copy=False)    
    
    
    
    motivo_fel = fields.Char(string='Motivo FEL')

    
    nota_debito = fields.Boolean(string="Nota de debito")
    comercial_id = fields.Many2one(string="Comercial", related='partner_id.user_id', readonly=True, store=True)

   
    def construir_correlativo_interno(self):
        
        correlativo = self.correlativo_fact_empresa
        diario = self.journal_id.codigo_establecimiento
        es_corr_interno = self.journal_id.generar_corr_interno
        
        if correlativo:
            pass
        else:
            if es_corr_interno == True:
                if  diario == 1:
                    corr = self.env['ir.sequence'].next_by_code('account.vesica')    
                    
                elif diario == 2:
                    corr = self.env['ir.sequence'].next_by_code('account.feedback')    
                    
                elif diario == 3:
                    corr = self.env['ir.sequence'].next_by_code('account.inversiones')
            else:    
        
                corr = False
            
            self.write({'correlativo_fact_empresa': corr})
    
   
    def _post(self, soft=True):
        action_post_local = super(AccountMove, self)._post(soft)
        
        
        self.solicitud_dte()
        
        
        return action_post_local
        
      

    def post(self):
        action_post_local = super(AccountMove, self)
        
        
        self.solicitud_dte()
        
        return action_post_local
        
        
        
        
    def captura_xml_proxy(self, xml_base64,  numeroDeAutorizacion):
        
        
        nombre_xml = f"{numeroDeAutorizacion}.xml"
        
        try:
                    
            #Guardar el archivo PDF en el directorio temporal
            xml_binary = base64.b64decode(xml_base64)
            attachment_vals = {
                        'name': nombre_xml,  # Nombre del archivo adjunto
                            'datas': xml_base64,     # Contenido del archivo adjunto
                            'type': 'binary',
                            'store_fname': nombre_xml,
                            'res_model':  self._name,
                            'res_id': self.id,
                            'mimetype': 'application/xml'
                        }
            attachment = self.env['ir.attachment'].sudo().create(attachment_vals)
        except Exception as e:
                        logging.exception("Error al guardar el archivo XML: %s", e)
        
                
    
    
    def captura_pdf_proxy(self, pdf_base64, correlativo, cliente, numeroDeAutorizacion, tipo_dte):
        
        corr = correlativo
        corr_amigable = ''
        if tipo_dte != 'FACT':
            nombre = tipo_dte
        else:
            nombre = 'FACTURA'
        
        print(corr)
        if corr == '':
            corr_amigable = numeroDeAutorizacion
        else:
            
            corr_amigable = corr
            
        logging.warning(corr_amigable)
        nombre_pdf = f"{nombre}-{corr_amigable}-{cliente}.pdf"
        logging.warning(nombre_pdf)
        
        if pdf_base64:
            try:
                        
                #Guardar el archivo PDF en el directorio temporal
                pdf_binary = base64.b64decode(pdf_base64)
                attachment_vals = {
                        'name': nombre_pdf,  # Nombre del archivo adjunto
                            'datas': pdf_base64,     # Contenido del archivo adjunto
                            'type': 'binary',
                            'store_fname': nombre_pdf,
                            'res_model':  self._name,
                            'res_id': self.id,
                            'mimetype': 'application/pdf'
                        }
                attachment = self.env['ir.attachment'].create(attachment_vals)
            except Exception as e:
                        logging.exception("Error al guardar el archivo PDF: %s", e)
        else:
            logging.warning("No se recibió ningún PDF en base64 en la respuesta.")
                
                

    def button_cancel(self):
        
        res = super(AccountMove, self).button_cancel()
        
        
        self.anular_dte()
        return res
    
    
    
    def obtener_token(self,usuario_proxy,clave_proxy):
        for rec in self:
            url = "https://proxy-fel.i3.gt/api/login"
            
            
            
            url = "https://proxy-fel.i3.gt/api/login"

            payload = {
            'email': usuario_proxy,
            'password': clave_proxy,
            'device': 'postman'
            }
            
            respuesta = requests.request("POST", url,  data=payload)
            respuesta_token = respuesta.text 
            respuesta_json = json.loads(respuesta.text)
            mi_token = respuesta_json["datos"]["token"]


        return mi_token
    
    
    def obtener_token_periodico(self, usuario_proxy,clave_proxy):
        cid = self.env.company.id
        data_company = self.env['res.company'].search([('id', '=', cid)])
        print(data_company.vat)
        #for rec in data_company
        if data_company.token_por_factura == False:
            if data_company.token_firma_fel == False:
                
                                    
                url = "https://proxy-fel.i3.gt/api/login"

                payload = {
                'email': usuario_proxy,
                'password': clave_proxy,
                'device': 'Odoo'
                }
            
                respuesta = requests.request("POST", url,  data=payload)
                respuesta_token = respuesta.text 
                respuesta_json = json.loads(respuesta.text)
                mi_token = respuesta_json["datos"]["token"]
                print(mi_token)
                values = {
                    'token_firma_fel':mi_token
                }
                data_company.sudo().update(values)
                
            else:
                mi_token = data_company.token_firma_fel
                return  mi_token
        
    

    def enviar_data (self, dict_factura, mi_token_es, url_solicitud):
        jdata2 = json.dumps(dict_factura)
        
        logging.warning(jdata2)
        
        headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {mi_token_es}"
        }
        
        response = requests.request("POST", url_solicitud, headers=headers, data=jdata2)

        
        logging.warning(response.text)
        return response
    
    def manejar_errores(self, mensaje, res_json, longitud_datos):
        print(longitud_datos)
        print(mensaje)
        
        if int(longitud_datos) > 0:                        
            error_txt = res_json["datos"][0].get("txt")
            error = res_json["datos"][0].get("error")

            if error_txt:
                print("err 1")
                print(error_txt)
                error = error_txt[0]
            elif error:
                print("err 2")
                error = error[0]
                print(error)
                
            self.message_post(body='<p>No se publicó la factura por error del certificador FEL:</p> <p><strong>'+mensaje+'</strong></p>'+'<strong>'+error+'</strong>')

        else:
            self.message_post(
                body='<p>No se publicó la factura por error del certificador FEL:</p> <p><strong>' +mensaje + '</strong></p>')
    
                    
    def solicitud_dte(self):
        
        
        if self.journal_id.generar_fel == True:
            for factura in self:
                
                if factura.journal_id.name == 'FACT FELPLEX/I3':
                    usuario_proxy = 'i3@i3.gt'
                    clave_proxy = 'i3@2023'
                    nit_emisor = 'DEMO'                    
                    es_pruebas_fel = 1
                
                else:
                    usuario_proxy = factura.company_id.usuario_proxy
                    clave_proxy = factura.company_id.clave_proxy
                    nit_emisor = factura.company_id.vat
                    if factura.company_id.es_pruebas_fel == True:
                        es_pruebas_fel = 1
                    else:
                        es_pruebas_fel = 0
                    
                user_id = self.invoice_user_id.name
                cid = self.env.company.name
                #logging.warning(user_id)
                usuario_app = f"{cid}/{user_id}"
                factura_fecha = factura.invoice_date
                factura_fecha_vencimiento = factura.invoice_date_due
                
                
                numero_linea = 0
                bien_servicio = "B"
                dict_factura = {}
                detalles = []
                detalle = []
                detalle_lineas = []
                
                #FACTOR DE DECIMALES
                getcontext().prec = 8
                
                mi_token_es = ''
                
                logging.warning(factura.invoice_date)
            
                if not factura.invoice_date:
                    raise ValidationError("El documento debe de tener una fecha de factura")
        
                if usuario_proxy == False or clave_proxy == False :
                    raise ValidationError("Para emitir una Facturas, es necesario que esté configurado los usuarios al Proxy FEL, contacta a tu administrador para que te ayude")
            
                if nit_emisor == False:
                    raise ValidationError("Para emitir una Factura es necesario que el cliente tenga un número de NIT, en Contactos")
                        
                if len(factura.invoice_line_ids) == 0:
                    raise ValidationError("El documento debe de poseer al menos una linea con valor mayor a 0")
                    
                if factura.company_id.token_por_factura == True:
                    mi_token_es = self.obtener_token(usuario_proxy,clave_proxy)    
                else:
                    mi_token_es = self.obtener_token_periodico(usuario_proxy,clave_proxy)
                
                
                
                url_solicitud = "https://proxy-fel.i3.gt/api/solicitud"
                url_solicitud_ncre = "https://proxy-fel.i3.gt/api/solicitud_ncre"
                
                if factura.partner_id.email:
                    correo_receptor = factura.partner_id.email
                else:
                    correo_receptor = ""
                
                
                
                # datos del receptor
                
                nit_receptor = factura.partner_id.vat
                
                direccion_receptor = factura.partner_id.street 
                codigo_postal_receptor = factura.partner_id.zip
                municipio_receptor = factura.partner_id.city 
                departamento_receptor = factura.partner_id.state_id.name 
                pais_receptor = factura.partner_id.country_id.code
                
                #obtiene las credeciales para hacer peticiones al proxy
                tipo_dte = factura.journal_id.tipo_dte
                generar_fel = factura.journal_id.generar_fel
                codigo_establecimiento = factura.journal_id.codigo_establecimiento
                es_corr_interno = factura.journal_id.generar_corr_interno
                
                incoterm = factura.invoice_incoterm_id.code
                correlativo = factura.correlativo_fact_empresa
                nombre_factura = factura.name 
                
                moneda_emisor = factura.currency_id.name
                nombre_receptor = factura.partner_id.name
                ncre_uuid_origen = factura.reversed_entry_id.numero_dte_uuid
                ncre_motivo = factura.motivo_fel
                monto_abono = ''
                
                #miramos los error en el body del cliente????? 
                error_historial = factura.journal_id.error_en_historial_fel
                
                token_proxy = factura.company_id.token_firma_fel
            
                descuento = 0
                precio_total_descuento = 0
                fix_precio_total_descuento = 0
                cliente = self.partner_id.name
                
                fix_precio_por_linea = 0
                precio_por_linea = 0

                impuesto_por_linea = 0
                fix_impuesto_por_linea = 0
                total_impuestos_lineas = 0
                precio_por_linea = 0
                total_precio_lineas = 0
                fix_precio_total_positivo = 0
                
                total_monto_linea = 0
                
                monto_gravable_linea = 0
                total_monto_gravable_lineas = 0
                fix_monto_gravable_linea = 0
                fix_total_monto_gravable_lineas = 0
                #valores fijos
                isr_proveedor_05 = 0.05
                isr_proveedor_07 = 0.07
                
                #rentenciones
                fix_total_retencion_lineas  = 0
                retencion_linea = 0
                total_retencion_lineas  = 0
                
                fix_total_menos_retenciones = 0
                total_menos_retenciones = 0
                
                cantidad_precio = 0
                fix_cantidad_precio = 0
                    
                #contador
                numero_linea = 0
            
                detalles= []
                
                
                
                        
                for lineas in factura.invoice_line_ids:
                    numero_linea += 1
                    
                    if lineas.price_unit == 0:
                        raise ValidationError("Para poder realizar el documento, los productos deben de tener un valor mayor a cero") 
                    
                    #empezamos a calcular el monto total a manoooo
                    fix_precio_por_linea =  Decimal(lineas.price_unit) * Decimal(lineas.quantity)
                    
                    precio_por_linea  = float(fix_precio_por_linea)
                    cantidad_precio = float(fix_precio_por_linea)
                    logging.warning("antes")
                    
                    logging.warning(precio_por_linea)
                    
                    # revisamos si hay descuento
                    if lineas.discount >= 1:
                        logging.warning("En descuento")
                        descuento = lineas.discount / 100
                        fix_precio_total_descuento =  Decimal(precio_por_linea) * Decimal(descuento)
                        precio_total_descuento = float(fix_precio_total_descuento)
                        fix_precio_por_linea = Decimal(precio_por_linea) - Decimal(fix_precio_total_descuento)
                        precio_por_linea  = float(fix_precio_por_linea)
                        
                        
                    
                    #revisamos las lineas una por una
                    
                    tax_ids_list_5 = [-12, -5, 12]
                    
                    tax_ids_list_7 = [12, -12, -5]
                    
                    tax_ids_odoo = []

                    # Iterar sobre los valores de impuestos
                    for tax in lineas.tax_ids:
                    # Agregar el valor real de impuesto a la lista
                        tax_ids_odoo.append(tax.amount)

                    logging.warning(tax_ids_odoo)
                    
                    
                    tax_ids_odoo.sort()
                    logging.warning(precio_por_linea)
                    
                    if tipo_dte in ["FACT", "FCAM", "NCRE"]:
                        fix_impuesto_por_linea = (Decimal(precio_por_linea)/Decimal(1.12))*Decimal(0.12)
                        impuesto_por_linea  = float(fix_impuesto_por_linea)
                        total_impuestos_lineas = Decimal(total_impuestos_lineas) + Decimal(impuesto_por_linea)
                        total_impuestos_lineas = float(total_impuestos_lineas)

                        fix_monto_gravable_linea = Decimal(precio_por_linea)/Decimal(1.12)
                        #logging.warning(fix_monto_gravable_linea)
                        monto_gravable_linea  = float(fix_monto_gravable_linea)
                        #logging.warning(monto_gravable_linea)
                        fix_total_monto_gravable_lineas = Decimal(total_monto_gravable_lineas)+Decimal(monto_gravable_linea)  
                        total_monto_gravable_lineas = float(fix_total_monto_gravable_lineas)
                        
                        
                        total_monto_linea = float(Decimal(lineas.price_total))
                        
                    elif tipo_dte == 'FESP':
                        if tax_ids_list_5 == tax_ids_odoo:
                        
                            #calculo del iva por linea
                            fix_impuesto_por_linea = (Decimal(precio_por_linea)/Decimal(1.12))*Decimal(0.12)
                            impuesto_por_linea  = float(fix_impuesto_por_linea)
                            total_impuestos_lineas = total_impuestos_lineas + impuesto_por_linea
                            logging.warning(total_impuestos_lineas)                        
                            
                            
                            #calclulo de base sin impuesto
                            fix_monto_gravable_linea = Decimal(precio_por_linea)/Decimal(1.12)
                            #logging.warning(fix_monto_gravable_linea)
                            monto_gravable_linea  = float(fix_monto_gravable_linea)
                            
                            
                            total_monto_linea = monto_gravable_linea +impuesto_por_linea
                            # logging.warning("///////////////////////")
                            
                            #calculo del isr
                            fix_retencion_linea = Decimal(fix_monto_gravable_linea) * Decimal(isr_proveedor_05)
                            # logging.warning(fix_retencion_linea)
                            fix_total_retencion_lineas = Decimal(fix_total_retencion_lineas) + Decimal(fix_retencion_linea)
                            total_retencion_lineas = float(fix_total_retencion_lineas)
                            # logging.warning(total_retencion_lineas)
                            #calcluo de total de la linea
                            fix_total_monto_gravable_lineas = Decimal(total_monto_gravable_lineas)+Decimal(monto_gravable_linea)  
                            total_monto_gravable_lineas = float(fix_total_monto_gravable_lineas)
                            # logging.warning(total_monto_gravable_lineas)
                            
                            #agregamos el resultado del fesp
                            fix_total_menos_retenciones = Decimal(fix_total_monto_gravable_lineas) - Decimal(fix_total_retencion_lineas)
                            total_menos_retenciones = float(fix_total_menos_retenciones)
                            # logging.warning(total_menos_retenciones)
                    # Excentos       
                    elif tipo_dte == 'FEXP':
                    
                        total_impuestos_lineas = 0
                        total_impuestos_lineas = float(total_impuestos_lineas)

                        fix_monto_gravable_linea = precio_por_linea
                        #logging.warning(fix_monto_gravable_linea)
                        monto_gravable_linea  = float(fix_monto_gravable_linea)                    
                                            
                        total_monto_linea = float(Decimal(lineas.price_total))
                                        
                    if tipo_dte == 'FCAM':                        
                        monto_abono = 1
                    elif tipo_dte == 'NCRE':                        
                        nombre_factura = factura.reversed_entry_id.name
                                        
                    if tipo_dte != 'FEXP':
                        incoterm = False
                    else:
                        nit_receptor = 'EXPORT'
                        if incoterm == False:
                            raise UserError('Las Facturas de Exportación deben de llevar que tipo de Incoterm se utilizará, el campo se ubica en Pestaña Otra Información / Incoterm')
                        
                    if factura.son_servicios == False:                        
                        if lineas.product_id.type == 'service':
                            bien_servicio = "S"
                        else:
                            bien_servicio = "B"
                    
                    elif factura.son_servicios == True:
                        bien_servicio = "S"       
                    
                    
                    if lineas.product_uom_id:
                        unidad_medida = "UND"

                    detalle_lineas = {
                        "numero_linea":numero_linea,
                        "bien_servicio":bien_servicio,
                        "cantidad":lineas.quantity,
                        "unidad_medida":unidad_medida,
                        "descripcion":lineas.name,
                        "precio_unitario":lineas.price_unit,
                        "precio":cantidad_precio,
                        "descuento":precio_total_descuento,
                        "impuesto":"IVA",
                        "codigo_unidad_gravable":factura.journal_id.codigo_unidad_gravable,
                        "monto_gravable":monto_gravable_linea,
                        "monto_impuesto":float(Decimal(impuesto_por_linea)),
                        "total":total_monto_linea                        
                    }                
                    
                    detalles.append(detalle_lineas)
                    fix_precio_total_positivo  += precio_por_linea
                    total_precio_lineas = float(fix_precio_total_positivo)
                    
                    
                    total_monto_gravable_lineas = Decimal(monto_gravable_linea) + Decimal(monto_gravable_linea)
                    total_monto_gravable_lineas = float(fix_total_monto_gravable_lineas)
                #exit()
                
                
                if es_corr_interno == False:
                    correlativo = ''
                    correlativo_name = ''
                
                    
                elif es_corr_interno == True:
                    if not correlativo:
                        raise UserError('El diario requiere Correlativo Interno, dar click en el botón, Crear Correlativo')

                    
                    correlativo_name = 'correlativo'
                
                #vamos a construir la cabeza una vez sepamos las lineas =)
                dict_factura = {
                    "usuario_app":usuario_app,
                    "es_pruebas":es_pruebas_fel,
                    "identificador_factura":nombre_factura,
                    "nit_emisor":nit_emisor,
                    "fh_emision": str(factura_fecha),
                    "moneda" : moneda_emisor,
                    "tipo_dte" : tipo_dte,
                    "codigo_establecimiento" : codigo_establecimiento,
                    "nit_receptor" : nit_receptor,
                    "nombre_receptor" : nombre_receptor,
                    "correo_receptor" :correo_receptor,
                    "direccion_receptor":direccion_receptor,
                    "codigo_postal_receptor":codigo_postal_receptor,
                    "municipio_receptor":municipio_receptor,
                    "incoterm":incoterm,
                    "departamento_receptor":departamento_receptor,
                    "pais_receptor":pais_receptor,
                    "nombre_impuesto":"IVA",                    
                    "total_impuesto":total_impuestos_lineas,
                    "total_menos_retenciones":total_menos_retenciones,
                    "total_isr":total_retencion_lineas,                
                    "total_sin_impuesto":total_monto_gravable_lineas,
                    "total_factura": total_precio_lineas,
                    "ncre_uuid_origen":ncre_uuid_origen,
                    "ncre_motivo":ncre_motivo,
                    "fecha_vencimiento":str(factura_fecha_vencimiento),
                    "monto_abono": monto_abono,
                    "adenda":[
                                {
                                    "name":correlativo_name,
                                    "value": correlativo
                                }
                            ],
                    "detalle":detalles
                    }                    
                
                logging.warning(dict_factura)
                
                ##Inicia la facturacion por diarios -> FACT
                if  dict_factura['tipo_dte'] in ["FACT", "FESP","FCAM","NCRE","FEXP"]: 
                    if dict_factura['tipo_dte']== "NCRE":
                        url_solicitud = url_solicitud_ncre
                    
                    print("|||||||||||||||||")                    
                    # se envia data al endpoint                
                    res_proxy = self.enviar_data(dict_factura, mi_token_es, url_solicitud)
                                        
                    
                    
                    res_json = json.loads(res_proxy.text)
                    # respuesta del endpoit 
                    status_code = res_proxy.status_code
                    mensaje = res_json["mensaje"]
                    exito = res_json["exito"]                    
                    
                    #manejando errores atipicos    
                    
                    if mensaje == 'Unauthenticated.':
                        raise UserError('Ups... parece que no Odoo no está conectado al a FEL GT, contacta a tu Implemantador de I3')
                    
                    
                    logging.warning(mensaje)
                    logging.warning(exito)
                    logging.warning(status_code)
                    
                    
                    error_txt = None
                    error = None

                    if int(status_code) == 200:                                              
                        if int(exito) == 1:
                            
                            self.state = "posted"      
                        
                            
                            pdf_base64 = res_json.get("datos", {}).get("pdf_base64")
                            pdf_enlace = res_json.get("datos", {}).get("pdf_url")
                            xml_base64 = res_json.get("datos", {}).get("xml_base64")
                            xml_enlace = res_json.get("datos", {}).get("xml_url")
                            numeroDeAutorizacion = res_json.get("datos", {}).get("uuid")
                            numero_dte_sat = res_json.get("datos", {}).get("numero")
                            serie = res_json.get("datos", {}).get("serie")
                            fh_certificacion = res_json.get("datos", {}).get("fecha_certificacion")
                            
                            
                            
                            self.serie_fel = serie                                                    
                            self.numero_dte_uuid = numeroDeAutorizacion
                            self.numero_dte_sat =  numero_dte_sat
                            self.enlace_fel_pdf = pdf_enlace
                            self.enlace_fel_xml =  xml_enlace
                            self.fh_emision_certificacion = fh_certificacion
                            
                            
                            if pdf_base64:
                                self.captura_pdf_proxy(pdf_base64, correlativo, cliente, numeroDeAutorizacion, tipo_dte)
                                
                            if xml_base64:
                                self.captura_xml_proxy(xml_base64, numeroDeAutorizacion)
                           
                            factura.message_post(body='REPUESTA DEL CERTIFICADOR:<p><strong>'+mensaje+'</strong></p>')

                        
                        elif int(exito) == 0:
                            logging.warning("en el segudno IF")
                            self.state = "draft"
                            longitud_datos = len(res_json["datos"])
                            self.manejar_errores( mensaje, res_json, longitud_datos)
                            
                    else:
                        logging.warning("en el tercer IF")
                        self.state = "draft"
                        longitud_datos = len(res_json["datos"])
                        self.manejar_errores( mensaje, res_json, longitud_datos)
                        
                        
    def anular_dte(self):
        url_anular ="https://proxy-fel.i3.gt/api/anular"
        
        if self.journal_id.generar_fel == True:
            
            for factura in self:                            
                if factura.journal_id.name == 'FACT FELPLEX/I3':
                    usuario_proxy = 'i3@i3.gt'
                    clave_proxy = 'i3@2023'
                    nit_emisor = 'DEMO'
                else:
                    usuario_proxy = factura.company_id.usuario_proxy
                    clave_proxy = factura.company_id.clave_proxy
                    nit_emisor = factura.company_id.vat
            #obtiene las credeciales para hacer peticiones al proxy
            
                user_id = self.invoice_user_id.name
                token_proxy = factura.company_id.token_firma_fel
                cid = self.env.company.name
                usuario_app = f"{cid}/{user_id}"
                
                if factura.company_id.token_por_factura == True:
                    mi_token_es = self.obtener_token(usuario_proxy,clave_proxy)    
                else:
                    mi_token_es = self.obtener_token_periodico(usuario_proxy,clave_proxy)

                
                if factura.motivo_fel == None or factura.motivo_fel == False:
                    raise ValidationError(" Para Anular la Factura : " + factura.numero_dte_uuid + " Hay que agregar el motivo en el campo Motivo Fel ubicado en la pestaña Otra Informacion)")
                dict_fact_anular = {

                    "motivo_anulacion":factura.motivo_fel,                
                    "uuid": factura.numero_dte_uuid,
                    "usuario_app":usuario_app,
                    
                }
                #logging.warning(type(dict_fact_anular))
                jdata2 = json.dumps(dict_fact_anular)
                #logging.warning(type(jdata2))
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {mi_token_es}'
                    }

                response = requests.request("POST", url_anular, headers=headers, data=jdata2)
                # print(response.text)
                response_json = json.loads(response.text)
                mensaje = response_json["mensaje"]
                exito = response_json["exito"]   
                
                
                if response.status_code == 200:
                    if int(exito) == 1:
                                                                        
                        pdf_base64 = response_json.get("datos", {}).get("pdf_base64")

                        factura.state = "cancel"
                        factura.message_post(body='REPUESTA DEL CERTIFICADOR:</p> <p><strong>'+mensaje+'</strong></p>')
                        
                        if pdf_base64:
                            corr_amigable = ''
                            
                            corr = self.correlativo_fact_empresa
                            cliente = self.partner_id.name
                            cliente_may = cliente.upper()
                            
                            if corr:
                                corr_amigable = corr
                            else:
                                corr_amigable = self.numero_dte_uuid
                                
                                
                            logging.warning(corr_amigable)
                            nombre_pdf = f"FACTURA-{corr_amigable}-{cliente_may}-ANULADA.pdf"
                            logging.warning(nombre_pdf)
                            
                            
                                            
                            #Guardar el archivo PDF en el directorio 
                            pdf_binary = base64.b64decode(pdf_base64)
                            attachment_vals = {
                                    'name': nombre_pdf,  # Nombre del archivo adjunto
                                    'datas': pdf_base64,     # Contenido del archivo adjunto
                                    'type': 'binary',
                                    'store_fname': nombre_pdf,
                                    'res_model':  self._name,
                                    'res_id': self.id,
                                    'mimetype': 'application/pdf'
                                    }
                            attachment = self.env['ir.attachment'].create(attachment_vals)
                                
                    elif int(exito) == 0:
                            logging.warning("en el segudno IF")
                            factura.state = "draft"
                            longitud_datos = len(response_json["datos"])
                            self.manejar_errores( mensaje, response_json, longitud_datos)
                            
                else:
                    logging.warning("en el tercer IF")
                    factura.state = "draft"
                    longitud_datos = len(response_json["datos"])
                    self.manejar_errores( mensaje, response_json, longitud_datos)    
                