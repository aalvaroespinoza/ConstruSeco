import os
from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import QSizeF, QMarginsF

def _fmt_moneda(valor: float) -> str:
    if valor is None: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generar_html_presupuesto(det: dict) -> str:
    """
    Genera el HTML representativo del documento para su posterior renderizado en PDF.
    Utiliza un diseño limpio, profesional y claro para impresiones A4 o PDF digitales.
    """
    
    # Resolving logo path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(base_dir, "assets", "logo.png").replace("\\", "/")
    
    # Preparar datos
    cli = det['cliente']
    num = det['numero_interno']
    fecha_emision = det['fecha_emision'][:16] if det['fecha_emision'] else ''
    fecha_vencimiento = det['fecha_vencimiento'][:16] if det['fecha_vencimiento'] else 'Sin vencimiento'
    estado = det['estado']
    
    # Color de estado
    color_estado = "#475569" # Default/Anulado
    if estado == "ACTIVO": color_estado = "#166534"
    elif estado == "VENCIDO": color_estado = "#991b1b"
    elif estado == "CONFIRMADO": color_estado = "#1e40af"
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, Helvetica, sans-serif; color: #1e293b; font-size: 13px; line-height: 1.5; margin: 0; padding: 0; }}
            .header {{ width: 100%; border-bottom: 2px solid #cbd5e1; padding-bottom: 16px; margin-bottom: 16px; }}
            .doc-type {{ font-size: 26px; font-weight: bold; color: #0f172a; margin: 0; }}
            .doc-num {{ font-size: 16px; color: #64748b; margin-top: 4px; }}
            .info-box {{ width: 48%; padding: 12px; background-color: #f8fafc; border: 1px solid #e2e8f0; }}
            .info-box h3 {{ margin: 0 0 8px 0; font-size: 12px; color: #475569; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
            .info-row {{ margin-bottom: 3px; font-size: 13px; }}
            .info-label {{ font-weight: bold; color: #64748b; }}
            .table {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 12px; }}
            .table th {{ background-color: #f1f5f9; color: #475569; text-align: left; padding: 8px; font-weight: bold; border-bottom: 2px solid #cbd5e1; }}
            .table td {{ padding: 8px; border-bottom: 1px solid #e2e8f0; }}
            .col-right {{ text-align: right; }}
            .col-center {{ text-align: center; }}
            .totals td {{ padding: 6px; font-size: 13px; }}
            .totals .label {{ text-align: right; color: #64748b; font-weight: bold; width: 70%; }}
            .totals .value {{ text-align: right; width: 30%; }}
            .totals .final-row td {{ font-size: 17px; font-weight: bold; color: #0f172a; border-top: 2px solid #cbd5e1; padding-top: 12px; }}
            .obs-box {{ margin-top: 20px; padding: 12px; background-color: #f8fafc; border-left: 4px solid #cbd5e1; }}
            .obs-title {{ font-weight: bold; color: #475569; margin-bottom: 4px; font-size: 11px; text-transform: uppercase; }}
            .footer {{ margin-top: 40px; text-align: center; color: #94a3b8; font-size: 10px; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
        </style>
    </head>
    <body>
        <table class="header" width="100%">
            <tr>
                <td width="50%" valign="middle">
                    <!-- Logo con dimensiones explícitas para QTextDocument -->
                    <img src="file:///{logo_path}" width="80" height="60" alt="Logo" />
                    <div style="margin-top: 6px; font-weight: bold; font-size: 15px; color: #334155;">CONSTRUSECO</div>
                </td>
                <td width="50%" valign="middle" align="right">
                    <div class="doc-type">PRESUPUESTO</div>
                    <div class="doc-num">#{num}</div>
                </td>
            </tr>
        </table>
        
        <table class="info-section">
            <tr>
                <td class="info-box" style="vertical-align: top;">
                    <h3>Datos del Cliente</h3>
                    <div class="info-row"><span class="info-label">Señor(es):</span> {cli['nombre_completo']}</div>
                    <div class="info-row"><span class="info-label">CUIT/DNI:</span> {cli['cuit_dni'] or '—'}</div>
                    <div class="info-row"><span class="info-label">Teléfono:</span> {cli['telefono'] or '—'}</div>
                    <div class="info-row"><span class="info-label">Cond. IVA:</span> {cli['condicion_iva'] or '—'}</div>
                </td>
                <td style="width: 4%;"></td> <!-- spacer -->
                <td class="info-box" style="vertical-align: top;">
                    <h3>Datos del Documento</h3>
                    <div class="info-row"><span class="info-label">Emisión:</span> {fecha_emision}</div>
                    <div class="info-row"><span class="info-label">Vencimiento:</span> {fecha_vencimiento}</div>
                    <div class="info-row"><span class="info-label">Estado:</span> <span style="color: {color_estado}; font-weight: bold;">{estado}</span></div>
                    <div class="info-row" style="margin-top: 8px; font-size: 11px; color: #64748b;">
                        <em>Los presupuestos tienen una validez estándar de 48 horas a partir de su emisión, sujetos a disponibilidad de stock al momento de la confirmación.</em>
                    </div>
                </td>
            </tr>
        </table>
        
        <table class="table">
            <thead>
                <tr>
                    <th style="width: 15%;">CÓDIGO</th>
                    <th style="width: 40%;">PRODUCTO</th>
                    <th class="col-center" style="width: 10%;">CANTIDAD</th>
                    <th class="col-center" style="width: 10%;">UNIDAD</th>
                    <th class="col-right" style="width: 12%;">PRECIO U.</th>
                    <th class="col-right" style="width: 13%;">SUBTOTAL</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for item in det['detalles']:
        cod = item.get('codigo_producto', '')
        desc = item.get('desc_producto', item.get('descripcion_producto', 'Producto'))
        cant = item.get('cantidad_unidad_venta', 0)
        uni = item.get('unidad_venta', 'u')
        precio = item.get('precio_unitario', 0.0)
        subt = item.get('subtotal', 0.0)
        
        # Descuento en la línea (opcional)
        desc_linea = ""
        if item.get('descuento_porcentaje', 0) > 0:
            desc_linea = f"<br><span style='font-size: 10px; color: #64748b;'>Dto: {item['descuento_porcentaje']:g}%</span>"
            
        html += f"""
                <tr>
                    <td>{cod}</td>
                    <td>{desc}</td>
                    <td class="col-center">{cant:g}</td>
                    <td class="col-center">{uni}</td>
                    <td class="col-right">$ {_fmt_moneda(precio)}{desc_linea}</td>
                    <td class="col-right">$ {_fmt_moneda(subt)}</td>
                </tr>
        """
        
    html += """
            </tbody>
        </table>
    """
    
    # Resumen Financiero
    subtotal = det.get('subtotal_bruto', 0.0)
    desc_gen_pct = det.get('descuento_general_porcentaje', 0.0)
    total_desc = det.get('total_descuento', 0.0)
    iva_monto = det.get('iva_monto', 0.0)
    total_final = det.get('total_final', 0.0)
    
    html += f"""
        <table class="totals">
            <tr>
                <td class="label">SUBTOTAL:</td>
                <td class="value">$ {_fmt_moneda(subtotal)}</td>
            </tr>
    """
    if desc_gen_pct > 0 or total_desc > 0:
        html += f"""
            <tr>
                <td class="label">DESCUENTO GENERAL ({desc_gen_pct:g}%):</td>
                <td class="value">-$ {_fmt_moneda(total_desc)}</td>
            </tr>
        """
    if iva_monto > 0:
        html += f"""
            <tr>
                <td class="label">IVA ({det.get('iva_porcentaje', 21.0):g}%):</td>
                <td class="value">$ {_fmt_moneda(iva_monto)}</td>
            </tr>
        """
        
    html += f"""
            <tr class="final-row">
                <td class="label">TOTAL FINAL:</td>
                <td class="value">$ {_fmt_moneda(total_final)}</td>
            </tr>
        </table>
    """
    
    obs = det.get('observaciones', '')
    if obs and obs.strip():
        # Clean potential newlines
        obs_html = obs.replace('\n', '<br>')
        html += f"""
        <div class="obs-box">
            <div class="obs-title">Observaciones</div>
            <div>{obs_html}</div>
        </div>
        """
        
    html += """
        <div class="footer">
            Este documento no es válido como factura. Los precios están sujetos a modificaciones sin previo aviso.<br>
            Generado automáticamente por el Sistema ConstruSeco.
        </div>
    </body>
    </html>
    """
    return html

def guardar_pdf_presupuesto(det: dict, ruta_destino: str) -> bool:
    """
    Genera el HTML y lo exporta a PDF en la ruta indicada.
    Retorna True si fue exitoso, lanza excepción en caso contrario.
    """
    html = generar_html_presupuesto(det)
    doc = QTextDocument()
    doc.setHtml(html)
    
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(ruta_destino)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    
    layout = QPageLayout()
    layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    layout.setOrientation(QPageLayout.Orientation.Portrait)
    layout.setMargins(QMarginsF(15, 15, 15, 15))
    printer.setPageLayout(layout)
    
    doc.print(printer)
    return True

