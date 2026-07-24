import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from PyQt6.QtCore import QSettings

from ui.core.theme import COLOR_PRIMARY, COLOR_TEXT_MAIN, COLOR_TEXT_SEC, COLOR_BORDER, COLOR_BG, COLOR_CARD_BG

def _fmt_moneda(valor: float) -> str:
    if valor is None: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generar_pdf_documento(det: dict, ruta_destino: str, tipo_documento: str = "PRESUPUESTO") -> bool:
    """
    Genera un PDF profesional utilizando ReportLab.
    Sirve tanto para PRESUPUESTO como para VENTA.
    """
    doc = SimpleDocTemplate(
        ruta_destino,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    
    # Estilos de párrafo
    style_normal = ParagraphStyle('Normal_Custom', parent=styles['Normal'], fontName='Helvetica', fontSize=12, leading=16)
    style_bold = ParagraphStyle('Bold_Custom', parent=style_normal, fontName='Helvetica-Bold')
    style_title = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor(COLOR_PRIMARY), alignment=TA_RIGHT)
    style_subtitle = ParagraphStyle('Subtitle', parent=style_normal, fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor(COLOR_TEXT_SEC), alignment=TA_RIGHT)
    
    style_company_name = ParagraphStyle('CompName', parent=style_bold, fontSize=16, textColor=colors.HexColor(COLOR_PRIMARY))
    style_company_desc = ParagraphStyle('CompDesc', parent=style_normal, fontSize=10, textColor=colors.HexColor(COLOR_TEXT_SEC))
    
    style_box_title = ParagraphStyle('BoxTitle', parent=style_bold, fontSize=13, textColor=colors.HexColor(COLOR_PRIMARY), spaceAfter=8)
    
    style_table_header = ParagraphStyle('TableHeader', parent=style_bold, fontSize=12, textColor=colors.HexColor(COLOR_CARD_BG), alignment=TA_CENTER)
    style_table_header_left = ParagraphStyle('TableHeaderL', parent=style_table_header, alignment=TA_LEFT)
    style_table_header_right = ParagraphStyle('TableHeaderR', parent=style_table_header, alignment=TA_RIGHT)
    
    style_table_cell = ParagraphStyle('TableCell', parent=style_normal, fontSize=12, alignment=TA_CENTER)
    style_table_cell_left = ParagraphStyle('TableCellL', parent=style_normal, fontSize=12, alignment=TA_LEFT)
    style_table_cell_right = ParagraphStyle('TableCellR', parent=style_normal, fontSize=12, alignment=TA_RIGHT)

    elements = []
    
    # 1. ENCABEZADO (Logo + Empresa vs Documento)
    from utils.paths import get_resource_path
    logo_path = get_resource_path("assets/logo.png")
    
    img = None
    if os.path.exists(logo_path):
        from reportlab.lib.utils import ImageReader
        img_reader = ImageReader(logo_path)
        img_w, img_h = img_reader.getSize()
        max_h = 2.0 * cm
        max_w = 3.3 * cm
        aspect_ratio = img_w / float(img_h)
        new_h = max_h
        new_w = new_h * aspect_ratio
        if new_w > max_w:
            new_w = max_w
            new_h = new_w / aspect_ratio
        img = Image(logo_path, width=new_w, height=new_h)
    
    num = det.get('numero_interno', '')
    
    settings = QSettings("ConstruSeco", "ERP")
    cuit = settings.value("empresa_cuit", "", type=str)
    dir_empresa = settings.value("empresa_direccion", "", type=str)
    tel = settings.value("empresa_telefono", "", type=str)
    
    # Empresa Info
    empresa_p = [
        Paragraph("CONSTRUSECO PEREYRA", style_company_name),
        Paragraph("Materiales para la Construcción en Seco", style_company_desc)
    ]
    
    parts = []
    if cuit: parts.append(f"CUIT: {cuit}")
    if dir_empresa: parts.append(dir_empresa)
    if tel: parts.append(f"Tel: {tel}")
    
    if parts:
        style_company_details = ParagraphStyle('CompDet', parent=style_company_desc, fontSize=10, textColor=colors.HexColor(COLOR_TEXT_SEC))
        det_text = " | ".join(parts)
        empresa_p.append(Paragraph(det_text, style_company_details))
    
    # Doc Info
    doc_info_p = [
        Paragraph(tipo_documento.upper(), style_title),
        Paragraph(f"Nº {num}", style_subtitle)
    ]
    
    header_data = [[img if img else "", empresa_p, doc_info_p]]
    header_table = Table(header_data, colWidths=[3.5*cm, 7.5*cm, 7*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor(COLOR_PRIMARY)),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    # 2. DATOS DEL CLIENTE Y METADATOS
    cli = det.get('cliente', {})
    
    cliente_info = [
        Paragraph("DATOS DEL CLIENTE", style_box_title),
        Paragraph(f"<b>Señor(es):</b> {cli.get('nombre_completo', '')}", style_normal),
        Paragraph(f"<b>CUIT/DNI:</b> {cli.get('cuit_dni', '') or '—'}", style_normal),
        Paragraph(f"<b>Teléfono:</b> {cli.get('telefono', '') or '—'}", style_normal),
        Paragraph(f"<b>Cond. IVA:</b> {cli.get('condicion_iva', '') or '—'}", style_normal)
    ]
    
    fecha_emision = det.get('fecha_emision', '')[:16]
    estado = det.get('estado', '')
    
    meta_info = [
        Paragraph("DATOS DEL DOCUMENTO", style_box_title),
        Paragraph(f"<b>Emisión:</b> {fecha_emision}", style_normal),
    ]
    
    if tipo_documento.upper() == "PRESUPUESTO":
        fecha_vencimiento = det.get('fecha_vencimiento', '')[:16] if det.get('fecha_vencimiento') else 'Sin vencimiento'
        meta_info.append(Paragraph(f"<b>Vencimiento:</b> {fecha_vencimiento}", style_normal))
        
    meta_info.append(Paragraph(f"<b>Estado:</b> {estado}", style_normal))
    
    if tipo_documento.upper() == "PRESUPUESTO":
        meta_info.append(Spacer(1, 10))
        meta_info.append(Paragraph(f"<font color='{COLOR_TEXT_SEC}' size='10'>* Validez de 48 hs desde su emisión.<br/>* Sujeto a disponibilidad de stock.</font>", style_normal))
        
    info_table = Table([[cliente_info, meta_info]], colWidths=[10*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor(COLOR_BG)),
        ('BOX', (0,0), (0,0), 1, colors.HexColor(COLOR_BORDER)),
        ('PADDING', (0,0), (0,0), 14),
        
        ('BACKGROUND', (1,0), (1,0), colors.HexColor(COLOR_CARD_BG)),
        ('PADDING', (1,0), (1,0), 14),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 25))
    
    # 3. TABLA DE DETALLES
    headers = [
        Paragraph("CÓDIGO", style_table_header_left),
        Paragraph("PRODUCTO", style_table_header_left),
        Paragraph("CANT.", style_table_header),
        Paragraph("UNID.", style_table_header),
        Paragraph("PRECIO U.", style_table_header_right),
        Paragraph("SUBTOTAL", style_table_header_right)
    ]
    
    table_data = [headers]
    
    for item in det.get('detalles', []):
        cod = str(item.get('codigo_producto', ''))
        desc = str(item.get('desc_producto', item.get('descripcion_producto', 'Producto')))
        cant = item.get('cantidad_unidad_venta', 0)
        uni = str(item.get('unidad_venta', 'u'))
        precio = item.get('precio_unitario', 0.0)
        subt = item.get('subtotal', 0.0)
        
        desc_linea = ""
        if item.get('descuento_porcentaje', 0) > 0:
            desc_linea = f"<br/><font color='red' size='10'>Dto: {item['descuento_porcentaje']:g}%</font>"
            
        row = [
            Paragraph(cod, style_table_cell_left),
            Paragraph(desc, style_table_cell_left),
            Paragraph(f"{cant:g}", style_table_cell),
            Paragraph(uni, style_table_cell),
            Paragraph(f"$ {_fmt_moneda(precio)}{desc_linea}", style_table_cell_right),
            Paragraph(f"$ {_fmt_moneda(subt)}", style_table_cell_right)
        ]
        table_data.append(row)
        
    t = Table(table_data, colWidths=[2.5*cm, 7.1*cm, 1.7*cm, 1.7*cm, 2.5*cm, 2.5*cm], repeatRows=1)
    
    ts = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor(COLOR_PRIMARY)),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('TOPPADDING', (0,0), (-1,0), 10),
    ])
    
    # Zebra styling and borders
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            bg_color = colors.HexColor(COLOR_BG)
        else:
            bg_color = colors.HexColor(COLOR_CARD_BG)
        ts.add('BACKGROUND', (0, i), (-1, i), bg_color)
        ts.add('LINEBELOW', (0, i), (-1, i), 1, colors.HexColor(COLOR_BORDER))
        ts.add('TOPPADDING', (0, i), (-1, i), 10)
        ts.add('BOTTOMPADDING', (0, i), (-1, i), 10)
        
    t.setStyle(ts)
    elements.append(t)
    elements.append(Spacer(1, 25))
    
    # 4. TOTALES FINALES
    subtotal = det.get('subtotal_bruto', 0.0)
    desc_gen_pct = det.get('descuento_general_porcentaje', 0.0)
    total_desc = det.get('total_descuento', 0.0)
    iva_monto = det.get('iva_monto', 0.0)
    total_final = det.get('total_final', 0.0)
    
    totals_data = [
        [Paragraph("SUBTOTAL:", style_table_cell_right), Paragraph(f"$ {_fmt_moneda(subtotal)}", style_bold)]
    ]
    
    if desc_gen_pct > 0 or total_desc > 0:
        totals_data.append([
            Paragraph(f"DESCUENTO ({desc_gen_pct:g}%):", style_table_cell_right), 
            Paragraph(f"<font color='red'>-$ {_fmt_moneda(total_desc)}</font>", style_bold)
        ])
        
    if iva_monto > 0:
        totals_data.append([
            Paragraph(f"IVA ({det.get('iva_porcentaje', 21.0):g}%):", style_table_cell_right), 
            Paragraph(f"$ {_fmt_moneda(iva_monto)}", style_bold)
        ])
        
    totals_data.append([
        Paragraph("<b>TOTAL FINAL:</b>", ParagraphStyle('TotFinal', parent=style_table_cell_right, textColor=colors.HexColor(COLOR_CARD_BG), fontSize=14)),
        Paragraph(f"<b>$ {_fmt_moneda(total_final)}</b>", ParagraphStyle('TotFinalV', parent=style_bold, textColor=colors.HexColor(COLOR_CARD_BG), fontSize=18, alignment=TA_RIGHT))
    ])
    
    totals_table = Table(totals_data, colWidths=[5*cm, 4*cm])
    tts = TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-2), 1, colors.HexColor(COLOR_BORDER)),
        ('PADDING', (0,0), (-1,-2), 10),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor(COLOR_PRIMARY)),
        ('PADDING', (0,-1), (-1,-1), 14),
    ])
    totals_table.setStyle(tts)
    
    # Observaciones
    obs = det.get('observaciones', '')
    if obs and obs.strip():
        obs_text = obs.replace('\n', '<br/>')
        obs_p = [
            Paragraph("OBSERVACIONES", style_box_title),
            Paragraph(obs_text, style_normal)
        ]
        obs_table = Table([[obs_p]], colWidths=[9*cm])
        obs_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), colors.HexColor('#f0fdf4')), # Dejar verde tenue por ser observaciones especiales
            ('BOX', (0,0), (0,0), 1, colors.HexColor('#bbf7d0')),
            ('PADDING', (0,0), (0,0), 14),
        ]))
    else:
        obs_table = ""
        
    bottom_block = Table([[obs_table, totals_table]], colWidths=[9*cm, 9*cm])
    bottom_block.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT')
    ]))
    
    elements.append(bottom_block) # Quitamos KeepTogether para evitar error en obs largas
    
    # Add page numbers and footer in a page template if desired, 
    # but for simplicity we can use SimpleDocTemplate's build callback.
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 10)
        canvas.setFillColor(colors.HexColor(COLOR_TEXT_SEC))
        canvas.setStrokeColor(colors.HexColor(COLOR_BORDER))
        canvas.line(1.5*cm, 2*cm, 19.5*cm, 2*cm)
        footer_text = "CONSTRUSECO PEREYRA - Documento orientativo, no válido como factura." if tipo_documento.upper() == "PRESUPUESTO" else "CONSTRUSECO PEREYRA - Documento no válido como factura fiscal."
        canvas.drawString(1.5*cm, 1.5*cm, footer_text)
        canvas.drawRightString(19.5*cm, 1.5*cm, f"Página {doc.page}")
        canvas.restoreState()

    try:
        doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False
