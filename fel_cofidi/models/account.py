# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round

from datetime import datetime
import base64
from lxml import etree
import requests
import re

#from import XMLSigner

import logging

class AccountMove(models.Model):
    _inherit = "account.move"

    firma_fel = fields.Char('Firma FEL', copy=False)
    serie_fel = fields.Char('Serie FEL', copy=False)
    numero_fel = fields.Char('Numero FEL', copy=False)
    consignatario_fel = fields.Many2one('res.partner', string="Consignatario o Destinatario FEL")
    comprador_fel = fields.Many2one('res.partner', string="Comprador FEL")
    exportador_fel = fields.Many2one('res.partner', string="Exportador FEL")
    incoterm_fel = fields.Many2one('account.incoterms', string="Incoterm FEL")
    pdf_fel = fields.Char('PDF FEL', copy=False)
    factura_original_id = fields.Many2one('account.move', string="Factura original FEL", domain="[('type', '=', 'out_invoice')]")

    def post(self):
        detalles = []
        subtotal = 0
        for factura in self:
            if factura.type in ['out_invoice', 'out_refund', 'in_invoice'] and factura.journal_id.generar_fel and not factura.firma_fel and factura.amount_total != 0:
                attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")

                NSMAP = {
                    "ds": "http://www.w3.org/2000/09/xmldsig#",
                    "dte": "http://www.sat.gob.gt/dte/fel/0.2.0",
                }

                NSMAP_REF = {
                    "cno": "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0",
                }

                NSMAP_ABONO = {
                    "cfc": "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0",
                }

                NSMAP_EXP = {
                    "cex": "http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0",
                }

                NSMAP_FE = {
                    "cfe": "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0",
                }

                DTE_NS = "{http://www.sat.gob.gt/dte/fel/0.2.0}"
                DS_NS = "{http://www.w3.org/2000/09/xmldsig#}"
                CNO_NS = "{http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0}"
                CFE_NS = "{http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0}"
                CEX_NS = "{http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0}"
                CFC_NS = "{http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0}"

                # GTDocumento = etree.Element(DTE_NS+"GTDocumento", {attr_qname: "http://www.sat.gob.gt/dte/fel/0.2.0"}, Version="0.4", nsmap=NSMAP)
                GTDocumento = etree.Element(DTE_NS+"GTDocumento", {}, Version="0.1", nsmap=NSMAP)
                SAT = etree.SubElement(GTDocumento, DTE_NS+"SAT", ClaseDocumento="dte")
                DTE = etree.SubElement(SAT, DTE_NS+"DTE", ID="DatosCertificados")
                DatosEmision = etree.SubElement(DTE, DTE_NS+"DatosEmision", ID="DatosEmision")

                tipo_documento_fel = factura.journal_id.tipo_documento_fel
                if tipo_documento_fel in ['FACT', 'FACM'] and factura.type == 'out_refund':
                    tipo_documento_fel = 'NCRE'

                moneda = "GTQ"
                if factura.currency_id.id != factura.company_id.currency_id.id:
                    moneda = "USD"

                fecha = factura.invoice_date.strftime('%Y-%m-%d')
                hora = fields.Datetime.context_timestamp(factura, timestamp=datetime.now()).strftime('%H:%M:%S')
                fecha_hora = fecha+'T'+hora
                DatosGenerales = etree.SubElement(DatosEmision, DTE_NS+"DatosGenerales", CodigoMoneda=moneda, FechaHoraEmision=fecha_hora, Tipo=tipo_documento_fel)
                if factura.tipo_gasto == 'importacion':
                    DatosGenerales.attrib['Exp'] = "SI"

                Emisor = etree.SubElement(DatosEmision, DTE_NS+"Emisor", AfiliacionIVA="GEN", CodigoEstablecimiento=str(factura.journal_id.codigo_establecimiento), CorreoEmisor=factura.company_id.email or '', NITEmisor=factura.company_id.vat.replace('-',''), NombreComercial=factura.journal_id.direccion.name, NombreEmisor=factura.company_id.name)
                DireccionEmisor = etree.SubElement(Emisor, DTE_NS+"DireccionEmisor")
                Direccion = etree.SubElement(DireccionEmisor, DTE_NS+"Direccion")
                Direccion.text = factura.journal_id.direccion.street or 'Ciudad'
                CodigoPostal = etree.SubElement(DireccionEmisor, DTE_NS+"CodigoPostal")
                CodigoPostal.text = factura.journal_id.direccion.zip or '01001'
                Municipio = etree.SubElement(DireccionEmisor, DTE_NS+"Municipio")
                Municipio.text = factura.journal_id.direccion.city or 'Guatemala'
                Departamento = etree.SubElement(DireccionEmisor, DTE_NS+"Departamento")
                Departamento.text = factura.journal_id.direccion.state_id.name if factura.journal_id.direccion.state_id else ''
                Pais = etree.SubElement(DireccionEmisor, DTE_NS+"Pais")
                Pais.text = factura.journal_id.direccion.country_id.code or 'GT'

                nit_receptor = 'CF'
                if factura.partner_id.vat:
                    nit_receptor = factura.partner_id.vat.replace('-','')
                if tipo_documento_fel == "FESP" and factura.partner_id.cui:
                    nit_receptor = factura.partner_id.cui
                Receptor = etree.SubElement(DatosEmision, DTE_NS+"Receptor", IDReceptor=nit_receptor, NombreReceptor=factura.partner_id.name)
                if factura.partner_id.nombre_facturacion_fel:
                    Receptor.attrib["NombreReceptor"] = factura.partner_id.nombre_facturacion_fel
                if factura.partner_id.email:
                    Receptor.attrib["CorreoReceptor"] = factura.partner_id.email
                if tipo_documento_fel == "FESP" and factura.partner_id.cui:
                    Receptor.attrib["TipoEspecial"] = "CUI"

                DireccionReceptor = etree.SubElement(Receptor, DTE_NS+"DireccionReceptor")
                Direccion = etree.SubElement(DireccionReceptor, DTE_NS+"Direccion")
                Direccion.text = (factura.partner_id.street or '') + ' ' + (factura.partner_id.street2 or '')
                # Direccion.text = " "
                CodigoPostal = etree.SubElement(DireccionReceptor, DTE_NS+"CodigoPostal")
                CodigoPostal.text = factura.partner_id.zip or '01001'
                Municipio = etree.SubElement(DireccionReceptor, DTE_NS+"Municipio")
                Municipio.text = factura.partner_id.city or 'Guatemala'
                Departamento = etree.SubElement(DireccionReceptor, DTE_NS+"Departamento")
                Departamento.text = factura.partner_id.state_id.name if factura.partner_id.state_id else ''
                Pais = etree.SubElement(DireccionReceptor, DTE_NS+"Pais")
                Pais.text = factura.partner_id.country_id.code or 'GT'

                if tipo_documento_fel not in ['NDEB', 'NCRE', 'RECI', 'NABN', 'FESP']:
                    Frases = etree.SubElement(DatosEmision, DTE_NS+"Frases")
                    Frase = etree.SubElement(Frases, DTE_NS+"Frase", CodigoEscenario="1", TipoFrase="1")
                    if factura.tipo_gasto == 'importacion':
                    	Frase = etree.SubElement(Frases, DTE_NS+"Frase", CodigoEscenario="1", TipoFrase="4")

                if tipo_documento_fel in ['NCRE'] and factura.tipo_gasto == 'importacion':
                    Frases = etree.SubElement(DatosEmision, DTE_NS+"Frases")
                    Frase = etree.SubElement(Frases, DTE_NS+"Frase", CodigoEscenario="1", TipoFrase="4")

                Items = etree.SubElement(DatosEmision, DTE_NS+"Items")

                linea_num = 0
                gran_subtotal = 0
                gran_total = 0
                gran_total_impuestos = 0
                cantidad_impuestos = 0
                for linea in factura.invoice_line_ids:

                    if linea.quantity * linea.price_unit == 0:
                        continue

                    linea_num += 1

                    tipo_producto = "B"
                    if linea.product_id.type == 'service':
                        tipo_producto = "S"
                    precio_unitario = linea.price_unit * (100-linea.discount) / 100
                    precio_sin_descuento = linea.price_unit
                    descuento = precio_sin_descuento * linea.quantity - precio_unitario * linea.quantity
                    precio_unitario_base = linea.price_subtotal / linea.quantity
                    total_timbre = 0
                    total_linea = (precio_unitario * linea.quantity) + total_timbre
                    total_linea_base = precio_unitario_base * linea.quantity
                    total_impuestos = total_linea - total_linea_base
                    cantidad_impuestos += len(linea.tax_ids)
                    

                    Item = etree.SubElement(Items, DTE_NS+"Item", BienOServicio=tipo_producto, NumeroLinea=str(linea_num))
                    Cantidad = etree.SubElement(Item, DTE_NS+"Cantidad")
                    Cantidad.text = str(linea.quantity)
                    UnidadMedida = etree.SubElement(Item, DTE_NS+"UnidadMedida")
                    UnidadMedida.text = "UNI"
                    Descripcion = etree.SubElement(Item, DTE_NS+"Descripcion")
                    Descripcion.text = linea.name
                    PrecioUnitario = etree.SubElement(Item, DTE_NS+"PrecioUnitario")
                    PrecioUnitario.text = '{:.6f}'.format(precio_sin_descuento)
                    Precio = etree.SubElement(Item, DTE_NS+"Precio")
                    Precio.text = '{:.6f}'.format(precio_sin_descuento * linea.quantity)
                    Descuento = etree.SubElement(Item, DTE_NS+"Descuento")
                    Descuento.text = '{:.6f}'.format(descuento)
                    if len(linea.tax_ids) != 0:
                        Impuestos = etree.SubElement(Item, DTE_NS+"Impuestos")
                        Impuesto = etree.SubElement(Impuestos, DTE_NS+"Impuesto")
                        NombreCorto = etree.SubElement(Impuesto, DTE_NS+"NombreCorto")
                        NombreCorto.text = "IVA"
                        CodigoUnidadGravable = etree.SubElement(Impuesto, DTE_NS+"CodigoUnidadGravable")
                        CodigoUnidadGravable.text = "1"
                        if factura.tipo_gasto == 'importacion':
                            CodigoUnidadGravable.text = "2"
                        MontoGravable = etree.SubElement(Impuesto, DTE_NS+"MontoGravable")
                        MontoGravable.text = '{:.2f}'.format(factura.currency_id.round(total_linea_base))
                        MontoImpuesto = etree.SubElement(Impuesto, DTE_NS+"MontoImpuesto")
                        MontoImpuesto.text = '{:.2f}'.format(factura.currency_id.round(total_impuestos))
                        if tipo_documento_fel not in ['NDEB', 'NCRE', 'RECI', 'NABN', 'FESP']:
                        	if len(linea.tax_ids) > 1:
                        		total_timbre = total_linea_base * 0.005
                        		Impuesto = etree.SubElement(Impuestos, DTE_NS+"Impuesto")
                        		NombreCorto = etree.SubElement(Impuesto, DTE_NS+"NombreCorto")
                        		NombreCorto.text = "TIMBRE DE PRENSA"
                        		CodigoUnidadGravable = etree.SubElement(Impuesto, DTE_NS+"CodigoUnidadGravable")
                        		CodigoUnidadGravable.text = "1"
                        		MontoGravable = etree.SubElement(Impuesto, DTE_NS+"MontoGravable")
                        		MontoGravable.text = '{:.2f}'.format(factura.currency_id.round(total_linea_base))
                        		MontoImpuesto = etree.SubElement(Impuesto, DTE_NS+"MontoImpuesto")
                        		MontoImpuesto.text = '{:.2f}'.format(factura.currency_id.round(total_timbre))
                    Total = etree.SubElement(Item, DTE_NS+"Total")
                    Total.text = '{:.2f}'.format(factura.currency_id.round(total_linea + total_timbre))

                    gran_total += factura.currency_id.round(total_linea + total_timbre)
                    gran_subtotal += factura.currency_id.round(total_linea_base)
                    gran_total_impuestos += factura.currency_id.round(total_impuestos + total_timbre)

                Totales = etree.SubElement(DatosEmision, DTE_NS+"Totales")
                if cantidad_impuestos > 0:
                    TotalImpuestos = etree.SubElement(Totales, DTE_NS+"TotalImpuestos")
                    TotalImpuesto = etree.SubElement(TotalImpuestos, DTE_NS+"TotalImpuesto", NombreCorto="IVA", TotalMontoImpuesto='{:.2f}'.format(factura.currency_id.round(gran_total_impuestos - total_timbre)))
                    if total_timbre > 0:
                        TotalImpuesto = etree.SubElement(TotalImpuestos, DTE_NS+"TotalImpuesto", NombreCorto="TIMBRE DE PRENSA", TotalMontoImpuesto='{:.2f}'.format(factura.currency_id.round(total_timbre)))
                GranTotal = etree.SubElement(Totales, DTE_NS+"GranTotal")
                GranTotal.text = '{:.2f}'.format(factura.currency_id.round(gran_total))

                if factura.company_id.adenda_fel:
                    Adenda = etree.SubElement(SAT, DTE_NS+"Adenda")
                    exec(factura.company_id.adenda_fel, {'etree': etree, 'Adenda': Adenda, 'factura': factura})

                # En todos estos casos, es necesario enviar complementos
                if tipo_documento_fel in ['NDEB', 'NCRE'] or tipo_documento_fel in ['FCAM'] or (tipo_documento_fel in ['FACT', 'FCAM'] and factura.tipo_gasto == 'importacion') or tipo_documento_fel in ['FESP']:  
                    Complementos = etree.SubElement(DatosEmision, DTE_NS+"Complementos")

                    if tipo_documento_fel in ['NDEB', 'NCRE']:
                        Complemento = etree.SubElement(Complementos, DTE_NS+"Complemento", IDComplemento="ReferenciasNota", NombreComplemento="Nota de Credito" if tipo_documento_fel == 'NCRE' else "Nota de Debito", URIComplemento="text")
                        if factura.factura_original_id.numero_fel:
                            ReferenciasNota = etree.SubElement(Complemento, CNO_NS+"ReferenciasNota", FechaEmisionDocumentoOrigen=str(factura.factura_original_id.invoice_date), MotivoAjuste="-", NumeroAutorizacionDocumentoOrigen=factura.factura_original_id.firma_fel, NumeroDocumentoOrigen=factura.factura_original_id.numero_fel, SerieDocumentoOrigen=factura.factura_original_id.serie_fel, Version="0.0", nsmap=NSMAP_REF)
                        else:
                            ReferenciasNota = etree.SubElement(Complemento, CNO_NS+"ReferenciasNota", RegimenAntiguo="Antiguo", FechaEmisionDocumentoOrigen=str(factura.factura_original_id.invoice_date), MotivoAjuste="-", NumeroAutorizacionDocumentoOrigen=factura.factura_original_id.firma_fel, NumeroDocumentoOrigen=factura.factura_original_id.name.split("-")[1], SerieDocumentoOrigen=factura.factura_original_id.name.split("-")[0], Version="0.0", nsmap=NSMAP_REF)

                    if tipo_documento_fel in ['FCAM']:
                        Complemento = etree.SubElement(Complementos, DTE_NS+"Complemento", IDComplemento="FCAM", NombreComplemento="AbonosFacturaCambiaria", URIComplemento="#AbonosFacturaCambiaria")
                        AbonosFacturaCambiaria = etree.SubElement(Complemento, CFC_NS+"AbonosFacturaCambiaria", Version="1", nsmap=NSMAP_ABONO)
                        Abono = etree.SubElement(AbonosFacturaCambiaria, CFC_NS+"Abono")
                        NumeroAbono = etree.SubElement(Abono, CFC_NS+"NumeroAbono")
                        NumeroAbono.text = "1"
                        FechaVencimiento = etree.SubElement(Abono, CFC_NS+"FechaVencimiento")
                        FechaVencimiento.text = str(factura.invoice_date_due)
                        MontoAbono = etree.SubElement(Abono, CFC_NS+"MontoAbono")
                        MontoAbono.text = '{:.2f}'.format(factura.currency_id.round(gran_total))

                    if tipo_documento_fel in ['FACT', 'NCRE', 'FCAM'] and factura.tipo_gasto == 'importacion':
                        Complemento = etree.SubElement(Complementos, DTE_NS+"Complemento", IDComplemento="text", NombreComplemento="text", URIComplemento="text")
                        Exportacion = etree.SubElement(Complemento, CEX_NS+"Exportacion", Version="1", nsmap=NSMAP_EXP)
                        NombreConsignatarioODestinatario = etree.SubElement(Exportacion, CEX_NS+"NombreConsignatarioODestinatario")
                        NombreConsignatarioODestinatario.text = factura.consignatario_fel.name if factura.consignatario_fel else "-"
                        DireccionConsignatarioODestinatario = etree.SubElement(Exportacion, CEX_NS+"DireccionConsignatarioODestinatario")
                        DireccionConsignatarioODestinatario.text = factura.consignatario_fel.street or "-" if factura.consignatario_fel else "-"
                        NombreComprador = etree.SubElement(Exportacion, CEX_NS+"NombreComprador")
                        NombreComprador.text = factura.comprador_fel.name if factura.comprador_fel else "-"
                        DireccionComprador = etree.SubElement(Exportacion, CEX_NS+"DireccionComprador")
                        DireccionComprador.text = factura.comprador_fel.street or "-" if factura.comprador_fel else "-"
                        INCOTERM = etree.SubElement(Exportacion, CEX_NS+"INCOTERM")
                        INCOTERM.text = factura.incoterm_fel.name if factura.incoterm_fel else ""
                        NombreExportador = etree.SubElement(Exportacion, CEX_NS+"NombreExportador")
                        NombreExportador.text = factura.exportador_fel.name if factura.exportador_fel else "-"
                        CodigoExportador = etree.SubElement(Exportacion, CEX_NS+"CodigoExportador")
                        CodigoExportador.text = factura.exportador_fel.ref or "-" if factura.exportador_fel else "-"

                    if tipo_documento_fel in ['FESP']:
                        total_isr = abs(factura.amount_tax)
                        
                        total_iva_retencion = total_impuestos

                        Complemento = etree.SubElement(Complementos, DTE_NS+"Complemento", IDComplemento="text", NombreComplemento="text", URIComplemento="text")
                        RetencionesFacturaEspecial = etree.SubElement(Complemento, CFE_NS+"RetencionesFacturaEspecial", Version="1", nsmap=NSMAP_FE)
                        RetencionISR = etree.SubElement(RetencionesFacturaEspecial, CFE_NS+"RetencionISR")
                        RetencionISR.text = str(total_isr)
                        RetencionIVA = etree.SubElement(RetencionesFacturaEspecial, CFE_NS+"RetencionIVA")
                        RetencionIVA.text = str(total_iva_retencion)
                        TotalMenosRetenciones = etree.SubElement(RetencionesFacturaEspecial, CFE_NS+"TotalMenosRetenciones")
                        TotalMenosRetenciones.text = str(factura.amount_total)

                xmls = etree.tostring(GTDocumento, encoding="UTF-8")
                xmls = xmls.decode("utf-8").replace("&amp;", "&").encode("utf-8")
                xmls_base64 = base64.b64encode(xmls)
                logging.warn(xmls)

                # cert = open("/home/odoo/100056865-cert.pem").read().encode('ascii')
                # key = open("/home/odoo/100056865.key").read().encode('ascii')
                #
                # signer = XMLSigner(c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315#WithComments')
                # signed_root = signer.sign(GTDocumento, key=key, cert=cert)
                #
                # signed_text = etree.tostring(signed_root, xml_declaration=True, encoding="UTF-8")
                # logging.warn(signed_text)
                #
                # signed_text_b64 = base64.b64encode(signed_text)
                # logging.warn(signed_text_b64)

                headers = { "Content-Type": "application/json" }
                data = {
                    "llave": factura.company_id.token_firma_fel,
                    "archivo": xmls_base64.decode("utf-8"),
                    "codigo": factura.company_id.vat.replace('-',''),
                    "alias": factura.company_id.usuario_fel,
                    "es_anulacion": "N"
                }
                r = requests.post('https://signer-emisores.feel.com.gt/sign_solicitud_firmas/firma_xml', json=data, headers=headers)
                logging.warn(r.text)
                firma_json = r.json()
                if firma_json["resultado"]:
                    # logging.warn(base64.b64decode(firma_json["archivo"]))

                    headers = {
                        "USUARIO": factura.company_id.usuario_fel,
                        "LLAVE": factura.company_id.clave_fel,
                        "IDENTIFICADOR": str(100000000+factura.id),
                        "Content-Type": "application/json",
                    }
                    data = {
                        "nit_emisor": factura.company_id.vat.replace('-',''),
                        "correo_copia": factura.company_id.email,
                        "xml_dte": firma_json["archivo"]
                    }
                    r = requests.post("https://certificador.feel.com.gt/fel/certificacion/v2/dte", json=data, headers=headers)
                    logging.warn(r.json())
                    certificacion_json = r.json()
                    if certificacion_json["resultado"]:
                        factura.firma_fel = certificacion_json["uuid"]
                        factura.ref = str(certificacion_json["serie"])+"-"+str(certificacion_json["numero"])
                        factura.serie_fel = certificacion_json["serie"]
                        factura.numero_fel = certificacion_json["numero"]
                        factura.pdf_fel = "https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid="+certificacion_json["uuid"]
                    else:
                        raise UserError(str(certificacion_json["descripcion_errores"]))
                else:
                    raise UserError(r.text)

        return super(AccountMove,self).post()
        
    def button_cancel(self):
        result = super(AccountMove, self).button_cancel()

        NSMAP = {
            "ds": "http://www.w3.org/2000/09/xmldsig#",
            "dte": "http://www.sat.gob.gt/dte/fel/0.2.0",
        }

        DTE_NS = "{http://www.sat.gob.gt/dte/fel/0.2.0}"
        DS_NS = "{http://www.w3.org/2000/09/xmldsig#}"
    
        for factura in self:
            if factura.journal_id.generar_fel and factura.firma_fel:

                tipo_documento_fel = factura.journal_id.tipo_documento_fel
                if tipo_documento_fel in ['FACT', 'FACM'] and factura.type == 'out_refund':
                    tipo_documento_fel = 'NCRE'

                nit_receptor = 'CF'
                if factura.partner_id.vat:
                    nit_receptor = factura.partner_id.vat.replace('-','')
                if tipo_documento_fel == "FESP" and factura.partner_id.cui:
                    nit_receptor = factura.partner_id.cui

                fecha = factura.invoice_date.strftime('%Y-%m-%d')
                hora = fields.Datetime.context_timestamp(factura, timestamp=datetime.now()).strftime('%H:%M:%S')
                fecha_hora = fecha+'T'+hora

                fecha_hoy = fields.Date.context_today(factura, timestamp=datetime.now())
                fecha_hora_hoy = fecha_hoy+'T'+hora

                GTAnulacionDocumento = etree.Element(DTE_NS+"GTAnulacionDocumento", {}, Version="0.1", nsmap=NSMAP)
                SAT = etree.SubElement(GTAnulacionDocumento, DTE_NS+"SAT", ClaseDocumento="dte")
                AnulacionDTE = etree.SubElement(SAT, DTE_NS+"AnulacionDTE", ID="DatosCertificados")
                DatosGenerales = etree.SubElement(AnulacionDTE, DTE_NS+"DatosGenerales", ID="DatosAnulacion", NumeroDocumentoAAnular=factura.firma_fel, NITEmisor=factura.company_id.vat.replace("-",""), IDReceptor=nit_receptor, FechaEmisionDocumentoAnular=fecha_hora, FechaHoraAnulacion=fecha_hora_hoy, MotivoAnulacion="Error")
                # Certificacion = etree.SubElement(AnulacionDTE, DTE_NS+"Certificacion")
                # NITCertificador = etree.SubElement(Certificacion, DTE_NS+"NITCertificador")
                # NITCertificador.text = "12521337"
                # NombreCertificador = etree.SubElement(Certificacion, DTE_NS+"NombreCertificador")
                # NombreCertificador.text = "INFILE, S.A."NombreCertificador = etree.SubElement(Certificacion, DTE_NS+"NombreCertificador")
                # NombreCertificador.text = "INFILE, S.A."

                xmls = etree.tostring(GTAnulacionDocumento, encoding="UTF-8")
                xmls = xmls.decode("utf-8").replace("&amp;", "&").encode("utf-8")
                xmls_base64 = base64.b64encode(xmls)
                logging.warn(xmls)

                headers = { "Content-Type": "application/json" }
                data = {
                    "llave": factura.journal_id.token_firma_fel,
                    "archivo": xmls_base64.decode("utf-8"),
                    "codigo": factura.company_id.vat.replace('-',''),
                    "alias": factura.journal_id.usuario_fel,
                    "es_anulacion": "Y"
                }
                r = requests.post('https://signer-emisores.feel.com.gt/sign_solicitud_firmas/firma_xml', json=data, headers=headers)
                logging.warn(r.text)
                firma_json = r.json()
                if firma_json["resultado"]:

                    headers = {
                        "USUARIO": factura.journal_id.usuario_fel,
                        "LLAVE": factura.journal_id.clave_fel,
                        "IDENTIFICADOR": factura.journal_id.code+str(factura.id),
                        "Content-Type": "application/json",
                    }
                    data = {
                        "nit_emisor": factura.company_id.vat.replace('-',''),
                        "correo_copia": factura.company_id.email,
                        "xml_dte": firma_json["archivo"]
                    }
                    r = requests.post("https://certificador.feel.com.gt/fel/anulacion/v2/dte", json=data, headers=headers)
                    logging.warn(r.text)
                    certificacion_json = r.json()
                    if not certificacion_json["resultado"]:
                        raise UserError(str(certificacion_json["descripcion_errores"]))
                else:
                    raise UserError(r.text)

    def button_draft(self):
        for factura in self:
            if factura.journal_id.generar_fel and factura.firma_fel:
                raise UserError("La factura ya fue enviada, por lo que ya no puede ser modificada")
            else:
                return super(AccountMove, self).button_draft()

class AccountJournal(models.Model):
    _inherit = "account.journal"

    generar_fel = fields.Boolean('Generar FEL',)
    tipo_documento_fel = fields.Selection([('FACT', 'FACT'), ('FCAM', 'FCAM'), ('FPEQ', 'FPEQ'), ('FCAP', 'FCAP'), ('FESP', 'FESP'), ('NABN', 'NABN'), ('RDON', 'RDON'), ('RECI', 'RECI'), ('NDEB', 'NDEB'), ('NCRE', 'NCRE')], 'Tipo de Documento FEL',)
    # usuario_fel = fields.Char('Usuario FEL',)
    # clave_fel = fields.Char('Clave FEL',)
    # token_firma_fel = fields.Char('Token Firma FEL',)

class ResCompany(models.Model):
    _inherit = "res.company"

    usuario_fel = fields.Char('Usuario FEL')
    clave_fel = fields.Char('Clave FEL')
    token_firma_fel = fields.Char('Token Firma FEL')
    frases_fel = fields.Text('Frases FEL')
    adenda_fel = fields.Text('Adenda FEL')
