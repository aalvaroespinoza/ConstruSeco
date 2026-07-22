from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QLabel, QPushButton, 
                             QHeaderView, QAbstractItemView, QMessageBox, QCheckBox,
                             QComboBox, QFrame, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
                             QDialog, QFormLayout, QButtonGroup, QCompleter, QSplitter,
                             QSplitterHandle, QStyledItemDelegate, QStackedWidget, QSizePolicy, QGridLayout)
from PyQt6.QtCore import Qt, QEvent, QTimer, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence, QColor, QFont, QPainter
from datetime import datetime, timedelta
import sqlite3
import re
from db.queries import subquery_atp, obtener_stock_producto
from ui.core.modal import ModalOverlay, ModalResult, DialogoModalIntegrado
from ui.modules.clientes.dialogs_clientes import DialogoFormularioCliente
from db import queries_clientes as qc

# --- Funciones Helper: Formato Argentino Seguros ---
def formato_arg(valor):
    """Convierte 10500.5 a '10.500,50' de forma segura."""
    try:
        if valor is None:
            valor = 0.0
        valor = float(valor)
        texto = f"{valor:,.2f}"
        return texto.replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

def parsear_arg(texto):
    """Parsea textos como '10.500,50' o '10,5' a float."""
    try:
        texto = str(texto).replace("$", "").replace("%", "").strip()
        if not texto:
            return 0.0
        texto_limpio = re.sub(r'[^\d.,-]', '', texto)
        if '.' in texto_limpio and ',' in texto_limpio:
            texto_limpio = texto_limpio.replace('.', '').replace(',', '.')
        elif ',' in texto_limpio:
            texto_limpio = texto_limpio.replace(',', '.')
        return float(texto_limpio)
    except ValueError:
        return 0.0

UMBRAL_STOCK_CRITICO = 5.0


class _HandleDivisorVenta(QSplitterHandle):
    """Handle sutil para que el divisor sea identificable sin invadir la vista."""

    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.setCursor(Qt.CursorShape.SplitVCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#F4F7FB"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#CBD5E1"))
        indicador_ancho = min(36, max(0, self.width() - 24))
        indicador_alto = 2
        painter.drawRoundedRect(
            (self.width() - indicador_ancho) // 2,
            (self.height() - indicador_alto) // 2,
            indicador_ancho,
            indicador_alto,
            1, 1
        )


class _AutoSelectDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            QTimer.singleShot(0, editor.selectAll)
        return editor

class _SugerenciaProductoDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        from PyQt6.QtCore import QSize
        return QSize(0, 56)

    def paint(self, painter, option, index):
        from PyQt6.QtGui import QTextDocument, QColor, QPixmap
        from PyQt6.QtCore import QRect, QRectF
        from PyQt6.QtWidgets import QStyle, QApplication
        
        painter.save()
        
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)
        
        p = index.data(Qt.ItemDataRole.UserRole)
        
        if not p:
            texto = index.data(Qt.ItemDataRole.DisplayRole)
            if texto:
                painter.setPen(option.palette.text().color())
                font = painter.font()
                font.setItalic(True)
                painter.setFont(font)
                rect = option.rect.adjusted(10, 0, -10, 0)
                painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, texto)
            painter.restore()
            return

        rect_img = QRect(option.rect.left() + 10, option.rect.top() + 8, 40, 40)
        rect_txt = QRect(rect_img.right() + 12, option.rect.top() + 8, option.rect.width() - 72, 40)
        
        pix = index.data(Qt.ItemDataRole.DecorationRole)
        if isinstance(pix, QPixmap) and not pix.isNull():
            painter.drawPixmap(rect_img, pix)
            painter.setPen(QColor("#E4E7EC"))
            painter.drawRect(rect_img)
        else:
            painter.fillRect(rect_img, QColor("#F8FAFC"))
            painter.setPen(QColor("#E4E7EC"))
            painter.drawRect(rect_img)
            painter.setPen(QColor("#1e293b"))
            font = painter.font()
            font.setPixelSize(18)
            painter.setFont(font)
            painter.drawText(rect_img, Qt.AlignmentFlag.AlignCenter, "📦")
            
        is_selected = option.state & QStyle.StateFlag.State_Selected
        text_color = option.palette.highlightedText().color().name() if is_selected else option.palette.text().color().name()
        sec_color = text_color if is_selected else "#475569"
        
        stock = p['stock']
        UMBRAL_STOCK_CRITICO = 5.0
        color_stock = text_color if is_selected else ("#ef4444" if stock <= UMBRAL_STOCK_CRITICO else sec_color)
        
        html = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="color: {text_color}; margin: 0; padding: 0;">
            <tr>
                <td style="font-size: 14px; padding-bottom: 2px;">
                    <span style="color: {sec_color}; font-size: 12px;">[{p['codigo']}]</span> 
                    <b>{p['desc']}</b>
                </td>
                <td align="right" style="font-size: 14px; font-weight: bold; color: {'#059669' if not is_selected else text_color};">
                    $ {formato_arg(p['precio_base'])}
                </td>
            </tr>
            <tr>
                <td style="font-size: 12px; color: {sec_color};">
                    Stock Disp: <span style="color: {color_stock}; font-weight: bold;">{stock:g}</span> {p['unidad_base']}
                </td>
                <td align="right" style="font-size: 11px; color: {sec_color};">
                    por {p['unidad_base']}
                </td>
            </tr>
        </table>
        """
        
        doc = QTextDocument()
        doc.setDefaultFont(painter.font())
        doc.setDocumentMargin(0)
        doc.setTextWidth(rect_txt.width())
        doc.setHtml(html)
        
        painter.translate(rect_txt.topLeft())
        doc.drawContents(painter, QRectF(0, 0, rect_txt.width(), rect_txt.height()))
        
        painter.restore()



class _SplitterVenta(QSplitter):
    def createHandle(self):
        return _HandleDivisorVenta(self.orientation(), self)


class DialogoVentaExitosa(DialogoModalIntegrado):
    def __init__(self, conn, id_documento, num_venta, cliente_txt, fecha_hora, cant_prods, cant_unidades, total, desconto_stock, is_presupuesto=False, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.id_documento = id_documento
        self.num_venta = num_venta
        self.is_presupuesto = is_presupuesto
        self.setWindowTitle("✓ Presupuesto Creado Correctamente" if is_presupuesto else "✓ Venta Realizada Correctamente")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # --- CÓDIGO DE VENTA ---
        lbl_codigo_tit = QLabel("Número de Presupuesto" if is_presupuesto else "Código de Operación")
        lbl_codigo_tit.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; text-transform: uppercase;")
        lbl_codigo_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_codigo = QLabel(f"#{num_venta}")
        lbl_codigo.setStyleSheet("color: #2563eb; font-size: 32px; font-weight: 900;")
        lbl_codigo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- RESUMEN COMPACTO ---
        resumen_frame = QFrame()
        resumen_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;")
        res_layout = QFormLayout(resumen_frame)
        res_layout.setContentsMargins(24, 24, 24, 24)
        res_layout.setSpacing(12)
        
        style_label = "color: #475569; font-size: 13px; font-weight: 600;"
        style_value = "color: #0f172a; font-size: 14px; font-weight: 500;"
        
        def add_row(k, v):
            lk = QLabel(k)
            lk.setStyleSheet(style_label)
            lv = QLabel(str(v))
            lv.setStyleSheet(style_value)
            lv.setWordWrap(True)
            res_layout.addRow(lk, lv)
            
        add_row("Cliente:", cliente_txt)
        add_row("Fecha y hora:", fecha_hora)
        add_row("Productos:", f"{cant_prods} ítem(s) ({cant_unidades:g} unidades)")
        add_row("Total final:", total)
        if is_presupuesto:
            add_row("Validez:", "48 horas desde su creación")
            
        add_row("Stock:", f"{'Descontado' if desconto_stock == 'Sí' else 'No descontado'}")
        
        # --- BOTONES ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setObjectName("btn_secundario")
        self.btn_cerrar.setFixedHeight(36)
        self.btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar.clicked.connect(self.accept)
        
        self.btn_preview = QPushButton("Vista Previa")
        self.btn_preview.setObjectName("btn_secundario")
        self.btn_preview.setFixedHeight(36)
        self.btn_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_preview.clicked.connect(self._vista_previa_pdf)
        
        self.btn_pdf = QPushButton("Generar PDF")
        self.btn_pdf.setObjectName("btn_primario")
        self.btn_pdf.setFixedHeight(36)
        self.btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pdf.clicked.connect(self._generar_pdf)
        
        btn_layout.addWidget(self.btn_cerrar)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_pdf)
        
        layout.addWidget(lbl_codigo_tit)
        layout.addWidget(lbl_codigo)
        layout.addWidget(resumen_frame)
        layout.addLayout(btn_layout)

    def _vista_previa_pdf(self):
        import tempfile, os
        from db.queries_presupuestos import obtener_detalle_presupuesto
        from utils.pdf_documento import generar_pdf_documento
        
        det = obtener_detalle_presupuesto(self.conn, self.id_documento)
        if not det: return
        tmp_path = os.path.join(tempfile.gettempdir(), f"preview_{self.id_documento}.pdf")
        tipo = "PRESUPUESTO" if self.is_presupuesto else "VENTA"
        if generar_pdf_documento(det, tmp_path, tipo):
            from ui.components.pdf_viewer import DialogoVistaPreviaPDF
            dlg = DialogoVistaPreviaPDF(tmp_path, self.window())
            from PyQt6.QtWidgets import QDialog
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self._generar_pdf()
                
    def _generar_pdf(self):
        import re
        from db.queries_presupuestos import obtener_detalle_presupuesto
        from utils.pdf_documento import generar_pdf_documento
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        det = obtener_detalle_presupuesto(self.conn, self.id_documento)
        if not det: return
        
        cli_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', det['cliente']['nombre_completo']).strip().replace(' ', '_')
        tipo = "PRESUPUESTO" if self.is_presupuesto else "VENTA"
        default_name = f"{tipo}_{det['numero_interno']}_{cli_name}.pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(self, f"Guardar {tipo} PDF", default_name, "Documentos PDF (*.pdf)")
        if file_path:
            try:
                if generar_pdf_documento(det, file_path, tipo):
                    QMessageBox.information(self, "Éxito", f"PDF generado correctamente en:\n{file_path}")
                else:
                    QMessageBox.critical(self, "Error", "Error al generar el PDF.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al generar el PDF:\n{e}")


class OperacionBaseWidget(QWidget):
    operacion_completada = pyqtSignal(str)
    estado_cambiado = pyqtSignal(object)
    
    def __init__(self, conexion_db, is_presupuesto=False, is_edicion=False, id_presupuesto_edicion=None):
        super().__init__()
        self.conn = conexion_db
        self.is_presupuesto = is_presupuesto
        self.is_edicion = is_edicion
        self.id_presupuesto_edicion = id_presupuesto_edicion
        self.carrito = [] 
        self.producto_en_foco = None 
        self.catalogo = []
        self.descuento_general = 0.0
        self.iva_aplicado = False
        self.iva_porcentaje = 21.0
        self.lista_clientes = []
        self._suspender_resultados = False
        
        self.cliente_seleccionado = None
        self.tipo_documento_seleccionado = 'PRESUPUESTO' if self.is_presupuesto else 'VENTA'
        
        self.migrar_esquema()
        self.init_ui()
        self.cargar_catalogo_memoria()
        self.cargar_autocompletado_clientes()
        self.configurar_atajos()
        
        if self.is_edicion and self.id_presupuesto_edicion:
            QTimer.singleShot(0, self._cargar_datos_edicion)
            
    def _cargar_datos_edicion(self):
        from db.queries_presupuestos import obtener_detalle_presupuesto
        det = obtener_detalle_presupuesto(self.conn, self.id_presupuesto_edicion)
        if not det: return
        
        # Cliente
        if det['cliente'] and det['cliente']['id_cliente']:
            cliente = {
                'id': det['cliente']['id_cliente'],
                'nombre': det['cliente']['nombre_completo'],
                'cuit': det['cliente'].get('cuit_dni', ''),
                'tel': det['cliente'].get('telefono', ''),
                'documento': det['cliente'].get('cuit_dni', '')
            }
            self.seleccionar_cliente(cliente)
            
        # Observaciones
        if det['observaciones']:
            self.input_observaciones.setText(det['observaciones'])
            
        # Descuento e IVA
        self.descuento_general = det['descuento_general_porcentaje']
        self.input_desc_gral.setText(f"{self.descuento_general:g}")
        self.iva_aplicado = det['iva_aplicado']
        self.chk_iva.setChecked(self.iva_aplicado)
        self.iva_porcentaje = det['iva_porcentaje']
        self.input_iva_porc.setText(f"{self.iva_porcentaje:g}")
        
        productos_no_encontrados = []
        
        # Productos
        for d in det['detalles']:
            codigo = d['codigo_producto']
            
            # Buscar info base del catálogo en memoria
            prod_base = None
            for p in self.catalogo:
                if p['codigo'] == codigo:
                    prod_base = p
                    break
            
            if not prod_base:
                productos_no_encontrados.append(f"{codigo} - {d['descripcion']}")
                continue
            
            # Factor de conversión (el original en detalle_documentos no se guarda, deducirlo o usar 1 si es base)
            factor = 1.0
            if d['cantidad_unidad_venta'] > 0:
                factor = d['cantidad_base'] / d['cantidad_unidad_venta']
                
            self.insertar_fila(
                prod={
                    'codigo': codigo,
                    'desc': prod_base['desc'],
                    'unidad_base': prod_base['unidad_base'],
                    'stock': prod_base['stock'],
                    'precio_base': prod_base['precio_base']
                },
                unidad_venta=d['unidad_venta'],
                factor_conversion=factor,
                cantidad=d['cantidad_unidad_venta'],
                cantidad_base=d['cantidad_base'],
                precio_unit_mostrado=d['precio_unitario']
            )
            # Aplicar descuento de linea
            if d['descuento_porcentaje'] > 0:
                self.tabla.item(self.tabla.rowCount() - 1, 6).setText(f"{d['descuento_porcentaje']:g}")
                self.carrito[-1]['descuento'] = d['descuento_porcentaje']
                
        self.actualizar_totales()
        
        if productos_no_encontrados:
            msg = "Los siguientes productos ya no existen en el catálogo y no pudieron ser cargados:\n\n"
            msg += "\n".join(f"• {p}" for p in productos_no_encontrados)
            QMessageBox.warning(self, "Productos no encontrados", msg)
        
    def migrar_esquema(self):
        from db.queries_ventas import migrar_esquema_ventas
        migrar_esquema_ventas(self.conn)

    def init_ui(self):
        # Tema Claro/Minimalista
        self.setStyleSheet("background-color: #F4F7FB;")
        
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', system-ui, sans-serif;
                color: #172033;
            }
            QFrame#tarjeta_blanca {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
            }
            QPushButton#btn_tipo_doc {
                background-color: #F8FAFC;
                color: #64748B;
                border: 1px solid #E2E8F0;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 13px;
                border-radius: 6px;
            }
            QPushButton#btn_tipo_doc:checked {
                background-color: #2563EB;
                color: #FFFFFF;
                border-color: #2563EB;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #FFFFFF;
                selection-background-color: #2563EB;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #3B82F6;
                background-color: #F8FAFC;
            }
            QLineEdit:disabled, QTextEdit:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
                border: 1px solid #E2E8F0;
            }
            QPushButton#btn_primario {
                background-color: #2563EB;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
                border: none;
            }
            QPushButton#btn_primario:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btn_primario:disabled {
                background-color: #94A3B8;
                color: #F8FAFC;
            }
            QPushButton#btn_secundario {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton#btn_secundario:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }
            QPushButton#btn_secundario:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
            }
            QPushButton#btn_peligro_sutil {
                background-color: #FFFFFF;
                color: #EF4444;
                border: 1px solid #FECACA;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton#btn_peligro_sutil:hover {
                background-color: #FEF2F2;
                border-color: #F87171;
            }
            QPushButton#btn_peligro_sutil_chico {
                background-color: #FFFFFF;
                color: #EF4444;
                border: 1px solid #FECACA;
                border-radius: 16px;
                padding: 4px 12px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton#btn_peligro_sutil_chico:hover {
                background-color: #FEF2F2;
                border-color: #F87171;
            }

            QCheckBox { 
                font-size: 14px; 
                color: #172033; 
                font-weight: 500;
            }
            QCheckBox::indicator { 
                width: 18px; 
                height: 18px; 
                border: 2px solid #CBD5E1;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #2563EB;
                border-color: #2563EB;
                image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+");
            }
            QTableWidget {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                gridline-color: #E2E8F0;
                background-color: #FFFFFF;
                outline: none;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #475569;
                font-weight: 600;
                font-size: 12px;
                border: none;
                border-right: 1px solid #E2E8F0;
                border-bottom: 2px solid #CBD5E1;
                padding: 8px;
            }
            QTableWidget::item {
                border-right: 1px solid #F1F5F9;
                border-bottom: 1px solid #F1F5F9;
                padding: 4px 8px;
                color: #1E293B;
            }
            QTableWidget::item:hover {
                background-color: #F8FAFC;
            }
            QTableWidget::item:selected {
                background-color: #EFF6FF;
                color: #1E3A8A;
                font-weight: 600;
            }
        """)

        # --- LAYOUT PRINCIPAL (SIN SCROLL PARA ENCABEZADO FIJO) ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        
        layout_principal = QVBoxLayout(scroll_content)
        layout_principal.setContentsMargins(24, 24, 24, 24)
        layout_principal.setSpacing(16)
        
        main_layout.addWidget(scroll_content)

        # --- 1. ENCABEZADO Y ESTADO ---
        ly_tit = QHBoxLayout()
        tit_txt = "Nuevo Presupuesto" if self.is_presupuesto else "Venta"
        sub_txt = "Creación de nuevo presupuesto" if self.is_presupuesto else "Venta directa rápida"
        ico_txt = "📄" if self.is_presupuesto else "🛒"
        
        from ui.components.encabezado import crear_encabezado_estandar
        ly_izq, btn_ayuda = crear_encabezado_estandar(ico_txt, tit_txt, sub_txt)
        btn_ayuda.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ayuda.clicked.connect(self._mostrar_ayuda)
        
        self.lbl_info_items = QLabel("🟢 Nueva operación")
        self.lbl_info_items.setStyleSheet("color: #0F172A; font-weight: 600; font-size: 14px; padding: 6px 12px; background: #E2E8F0; border-radius: 16px;")
        
        self.btn_vaciar_carrito = QPushButton("Vaciar [F11]")
        self.btn_vaciar_carrito.setObjectName("btn_peligro_sutil_chico")
        self.btn_vaciar_carrito.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_vaciar_carrito.clicked.connect(self.vaciar_carrito_directo)
        self.btn_vaciar_carrito.setMinimumHeight(38)
        
        ly_tit.addLayout(ly_izq)
        ly_tit.addStretch()
        ly_tit.addWidget(self.btn_vaciar_carrito)
        ly_tit.addWidget(self.lbl_info_items)
        ly_tit.addWidget(btn_ayuda)
        
        layout_principal.addLayout(ly_tit)

        # --- 2. SECCIÓN CLIENTE ---
        frm_cliente = QFrame()
        frm_cliente.setObjectName("tarjeta_blanca")
        ly_cliente = QHBoxLayout(frm_cliente)
        ly_cliente.setContentsMargins(12, 8, 12, 8)
        ly_cliente.setSpacing(12)
        
        lbl_cli_tit = QLabel("1. CLIENTE")
        lbl_cli_tit.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;")
        ly_cliente.addWidget(lbl_cli_tit)

        self.widget_busqueda_cliente = QWidget()
        layout_busq_cli = QHBoxLayout(self.widget_busqueda_cliente)
        layout_busq_cli.setContentsMargins(0, 0, 0, 0)
        layout_busq_cli.setSpacing(8)
        
        self.input_cliente = QLineEdit()
        self.input_cliente.setPlaceholderText("Buscar por nombre o CUIT (F3)...")
        self.input_cliente.setMinimumHeight(38)
        self.input_cliente.setStyleSheet("QLineEdit { border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px; font-size: 13px; background: #F8FAFC; } QLineEdit:focus { border: 1px solid #3B82F6; background: #FFFFFF; }")
        self.input_cliente.returnPressed.connect(self.procesar_input_cliente)
        
        self.btn_nuevo_cliente = QPushButton("+ Nuevo")
        self.btn_nuevo_cliente.setObjectName("btn_secundario")
        self.btn_nuevo_cliente.setMinimumHeight(38)
        self.btn_nuevo_cliente.setStyleSheet("""
            QPushButton#btn_secundario {
                padding: 0px 16px;
                font-size: 13px;
                text-align: center;
                qproperty-iconSize: 16px;
            }
        """)
        self.btn_nuevo_cliente.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo_cliente.clicked.connect(self.modal_nuevo_cliente)
        
        layout_busq_cli.addWidget(self.input_cliente)
        layout_busq_cli.addWidget(self.btn_nuevo_cliente)
        
        self.widget_tarjeta_cliente = QFrame()
        self.widget_tarjeta_cliente.setStyleSheet("background-color: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 6px;")
        self.widget_tarjeta_cliente.setMinimumHeight(38)
        layout_tarjeta_cli = QHBoxLayout(self.widget_tarjeta_cliente)
        layout_tarjeta_cli.setContentsMargins(12, 0, 8, 0)
        layout_tarjeta_cli.setSpacing(12)
        
        self.lbl_nombre_cliente = QLabel("<b>Nombre Cliente</b>")
        self.lbl_nombre_cliente.setStyleSheet("color: #0F172A; font-size: 13px;")
        self.lbl_datos_cliente = QLabel("CUIT/DNI - Tel")
        self.lbl_datos_cliente.setStyleSheet("color: #64748B; font-size: 12px;")
        
        from ui.components.boton_x import BotonCerrarX
        self.btn_quitar_cliente = BotonCerrarX()
        self.btn_quitar_cliente.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quitar_cliente.clicked.connect(self.deseleccionar_cliente)
        
        layout_tarjeta_cli.addWidget(self.lbl_nombre_cliente)
        layout_tarjeta_cli.addWidget(self.lbl_datos_cliente)
        layout_tarjeta_cli.addWidget(self.btn_quitar_cliente)
        self.widget_tarjeta_cliente.setVisible(False)
        
        ly_cliente.addWidget(self.widget_busqueda_cliente, stretch=1)
        ly_cliente.addWidget(self.widget_tarjeta_cliente, stretch=1)
        
        layout_principal.addWidget(frm_cliente)

        # --- 3. SECCIÓN PRODUCTOS ---
        self.contenedor_tabla = QFrame()
        self.contenedor_tabla.setObjectName("tarjeta_blanca")
        layout_tabla = QVBoxLayout(self.contenedor_tabla)
        layout_tabla.setContentsMargins(20, 16, 20, 16)
        layout_tabla.setSpacing(12)
        
        lbl_prod_tit = QLabel("2. PRODUCTOS")
        lbl_prod_tit.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;")
        layout_tabla.addWidget(lbl_prod_tit)
        # --- ZONA CENTRAL: BUSCADOR + CARRITO ---
        # 1. Buscador y Cantidad
        layout_buscador = QHBoxLayout()
        layout_buscador.setContentsMargins(0, 0, 0, 0)
        layout_buscador.setSpacing(16)
        
        # Contenedor del buscador
        self.frame_buscador = QFrame()
        self.frame_buscador.setObjectName("frame_buscador")
        self.frame_buscador.setStyleSheet("""
            QFrame#frame_buscador {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
            }
        """)
        
        ly_busq_inner = QHBoxLayout(self.frame_buscador)
        ly_busq_inner.setContentsMargins(0, 0, 0, 0)
        ly_busq_inner.setSpacing(0)
        
        lbl_lupa = QLabel("🔍")
        lbl_lupa.setStyleSheet("font-size: 18px; padding-left: 16px; background-color: transparent; border: none;")
        lbl_lupa.setFixedSize(44, 48)
        
        self.input_buscador = QLineEdit()
        self.input_buscador.setPlaceholderText("Buscar producto por código o descripción... (F2)")
        self.input_buscador.setObjectName("input_buscador")
        self.input_buscador.setMinimumHeight(48)
        self.input_buscador.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                font-size: 16px;
                padding-left: 8px;
                color: #0F172A;
            }
        """)
        self.input_buscador.textChanged.connect(self.on_buscador_text_changed)
        self.input_buscador.installEventFilter(self)
        
        self.btn_limpiar_buscador = QPushButton("✕")
        self.btn_limpiar_buscador.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_limpiar_buscador.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_limpiar_buscador.setFixedSize(36, 48)
        self.btn_limpiar_buscador.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94A3B8;
                border: none;
                font-size: 16px;
                font-weight: bold;
                padding-right: 12px;
            }
            QPushButton:hover {
                color: #EF4444;
            }
        """)
        self.btn_limpiar_buscador.setVisible(False)
        self.btn_limpiar_buscador.clicked.connect(self.limpiar_buscador_producto)
        
        ly_busq_inner.addWidget(lbl_lupa)
        ly_busq_inner.addWidget(self.input_buscador)
        ly_busq_inner.addWidget(self.btn_limpiar_buscador)
        
        self.combo_unidad = QComboBox()
        self.combo_unidad.setFixedWidth(140)
        self.combo_unidad.setMinimumHeight(48)
        self.combo_unidad.setVisible(False)
        self.combo_unidad.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_unidad.installEventFilter(self)
        self.combo_unidad.currentIndexChanged.connect(self.on_unidad_cambiada)
        self.combo_unidad.setStyleSheet("QComboBox { border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px; font-size: 15px; background: #FFFFFF; }")
        
        self.caja_cant_frame = QFrame()
        self.caja_cant_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
            }
        """)
        self.caja_cant_frame.setFixedHeight(48)
        caja_cant = QHBoxLayout(self.caja_cant_frame)
        caja_cant.setContentsMargins(12, 4, 4, 4)
        caja_cant.setSpacing(12)
        
        self.lbl_cant = QLabel("CANT:")
        self.lbl_cant.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 700; border: none; background: transparent;")
        
        self.input_cantidad = QLineEdit()
        self.input_cantidad.setPlaceholderText("1")
        self.input_cantidad.setFixedWidth(60)
        self.input_cantidad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_cantidad.setObjectName("input_cantidad")
        self.input_cantidad.setEnabled(False)
        self.input_cantidad.returnPressed.connect(self.agregar_al_carrito)
        self.input_cantidad.installEventFilter(self)
        self.input_cantidad.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                background-color: #FFFFFF;
                padding: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
        """)
        
        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.setObjectName("btn_primario")
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar.clicked.connect(self.agregar_al_carrito)
        self.btn_agregar.setFixedHeight(36)
        self.btn_agregar.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        
        caja_cant.addWidget(self.lbl_cant)
        caja_cant.addWidget(self.input_cantidad)
        caja_cant.addWidget(self.btn_agregar)
        
        lbl_v_por = QLabel("Por:")
        lbl_v_por.setStyleSheet("color: #64748B; font-weight: 600; font-size: 14px;")
        
        layout_buscador.addWidget(self.frame_buscador, stretch=1)
        layout_buscador.addWidget(lbl_v_por, 0, Qt.AlignmentFlag.AlignRight)
        self.lbl_vender_por = layout_buscador.itemAt(layout_buscador.count() - 1).widget()
        self.lbl_vender_por.setVisible(False)
        layout_buscador.addWidget(self.combo_unidad)
        layout_buscador.addWidget(self.caja_cant_frame)
        
        layout_tabla.addLayout(layout_buscador)
        
        # Panel de resultados (Overlay)
        self.panel_resultados = QFrame(self, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.panel_resultados.setObjectName("panel_resultados")
        self.panel_resultados.setStyleSheet("""
            QFrame#panel_resultados {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }
            QListWidget {
                border: none;
                background-color: #ffffff;
                outline: none;
                font-size: 14px;
            }
            QListWidget::item {
                border-bottom: 1px solid #F1F5F9;
                padding: 2px 0px;
                background-color: #ffffff;
                color: #172033;
            }
            QListWidget::item:selected {
                background-color: #2563EB;
                color: #FFFFFF;
            }
            QListWidget::item:hover {
                background-color: #F0F7FF;
                color: #172033;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 5)
        self.panel_resultados.setGraphicsEffect(shadow)
        
        panel_layout = QVBoxLayout(self.panel_resultados)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        
        self.lista_resultados = QListWidget()
        self.sugerencias_delegate = _SugerenciaProductoDelegate(self.lista_resultados)
        self.lista_resultados.setItemDelegate(self.sugerencias_delegate)
        self.lista_resultados.itemClicked.connect(self.on_resultado_clickeado)
        self.lista_resultados.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        panel_layout.addWidget(self.lista_resultados)
        
        # --- TABLA (CARRITO) Y ESTADO VACÍO ---
        cabecera_tabla = QHBoxLayout()
        cabecera_tabla.setContentsMargins(0, 8, 0, 8)
        
        lbl_tit_tabla = QLabel("Detalle de la Operación")
        lbl_tit_tabla.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A; text-transform: uppercase; letter-spacing: 0.5px;")
        
        self.lbl_resumen_rapido = QLabel("0 productos · 0 unidades")
        self.lbl_resumen_rapido.setStyleSheet("color: #64748B; font-weight: 600; font-size: 14px; background: #F8FAFC; padding: 8px 16px; border-radius: 14px; border: 1px solid #E2E8F0;")
        
        cabecera_tabla.addWidget(lbl_tit_tabla)
        cabecera_tabla.addStretch()
        cabecera_tabla.addWidget(self.lbl_resumen_rapido)
        
        layout_tabla.addLayout(cabecera_tabla)
        
        self.stack_tabla = QStackedWidget()
        
        # Estado Vacío (Moderno)
        wid_vacio = QWidget()
        ly_vacio = QVBoxLayout(wid_vacio)
        ly_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_vacio_ico = QLabel("🛒")
        lbl_vacio_ico.setStyleSheet("font-size: 48px; color: #94A3B8;")
        lbl_vacio_ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_vacio_tit = QLabel("Carrito vacío")
        lbl_vacio_tit.setStyleSheet("font-size: 18px; font-weight: 700; color: #334155; margin-top: 12px;")
        lbl_vacio_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_vacio_sub = QLabel("Busque y agregue un producto para comenzar.")
        lbl_vacio_sub.setStyleSheet("font-size: 14px; color: #64748B; margin-top: 4px;")
        lbl_vacio_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ly_vacio.addWidget(lbl_vacio_ico)
        ly_vacio.addWidget(lbl_vacio_tit)
        ly_vacio.addWidget(lbl_vacio_sub)
        
        self.lbl_estado_vacio = wid_vacio
        self.lbl_estado_vacio.setStyleSheet("background-color: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 6px;")
        self.stack_tabla.addWidget(self.lbl_estado_vacio)
        
        # Tabla Principal
        self.tabla = QTableWidget(0, 9)
        self.tabla.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Cantidad", "Equival.", "Precio Unit.", "Desc. (%)", "Subtotal", ""])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(48) # Filas más legibles
        self.tabla.setShowGrid(True)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers) # Edición rápida (1 clic)
        self.tabla.setAttribute(Qt.WidgetAttribute.WA_Hover)
        
        self.auto_select_delegate = _AutoSelectDelegate(self.tabla)
        self.tabla.setItemDelegateForColumn(3, self.auto_select_delegate)
        self.tabla.setItemDelegateForColumn(6, self.auto_select_delegate)
        
        # Ajustes de ancho priorizando la descripcion (adaptado HD 125-150%)
        self.tabla.setColumnWidth(0, 100)
        self.tabla.setColumnWidth(2, 85)
        self.tabla.setColumnWidth(3, 95)
        self.tabla.setColumnWidth(4, 100)
        self.tabla.setColumnWidth(5, 130)
        self.tabla.setColumnWidth(6, 85)
        self.tabla.setColumnWidth(7, 140)
        self.tabla.setColumnWidth(8, 48) # Eliminación moderna sin ocupar columnas enormes
        
        self.tabla.itemChanged.connect(self.celda_editada)
        self.stack_tabla.addWidget(self.tabla)
        
        # Inicialmente mostrar el estado vacío
        self.stack_tabla.setCurrentIndex(0)
        
        layout_tabla.addWidget(self.stack_tabla, stretch=1)

        self.contenedor_tabla.setMinimumHeight(200)
        layout_principal.addWidget(self.contenedor_tabla, stretch=1)

        # --- 4. BARRA INFERIOR (RESUMEN Y ACCIONES) ---
        self.contenedor_footer = QFrame()
        self.contenedor_footer.setObjectName("tarjeta_blanca")
        self.contenedor_footer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout_footer = QHBoxLayout(self.contenedor_footer)
        layout_footer.setContentsMargins(16, 12, 16, 12)
        layout_footer.setSpacing(24)
        
        # --- INICIALIZAR COMPONENTES COMPARTIDOS/NECESARIOS ---
        
        self.input_observaciones = QLineEdit()
        self.input_observaciones.setPlaceholderText("Observaciones (opcional)...")
        self.input_observaciones.setMinimumHeight(36)
        self.input_observaciones.setStyleSheet("border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; padding: 0 10px; background-color: #F8FAFC;")
        
        self.combo_validez = QComboBox()
        self.combo_validez.addItems(["48 horas", "15 días", "30 días", "7 días", "Hasta agotar stock"])
        self.combo_validez.setStyleSheet("border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; padding: 4px 10px; background-color: #F8FAFC;")
        
        self.lbl_subtotal = QLabel("$ 0,00")
        self.lbl_subtotal.setStyleSheet("font-size: 16px; font-weight: 600; color: #334155;")
        
        self.input_desc_gral = QLineEdit("0")
        self.input_desc_gral.setFixedWidth(60)
        self.input_desc_gral.setFixedHeight(30)
        self.input_desc_gral.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_desc_gral.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 4px; font-size: 13px; background-color: #FFFFFF; color: #2563EB; font-weight: bold; padding: 0;")
        self.input_desc_gral.editingFinished.connect(self.on_descuento_general_editado)
        self.input_desc_gral.installEventFilter(self)
        
        self.lbl_monto_desc = QLabel("-$ 0,00")
        self.lbl_monto_desc.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: 600;")
        
        self.chk_iva = QCheckBox("IVA:")
        self.chk_iva.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 700; text-transform: uppercase;")
        self.chk_iva.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_iva.stateChanged.connect(self.on_iva_toggled)
        
        self.input_iva_porc = QLineEdit("21")
        self.input_iva_porc.setFixedWidth(60)
        self.input_iva_porc.setFixedHeight(30)
        self.input_iva_porc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_iva_porc.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 4px; font-size: 13px; background-color: #FFFFFF; padding: 0;")
        self.input_iva_porc.setEnabled(False)
        self.input_iva_porc.editingFinished.connect(self.on_iva_editado)
        self.input_iva_porc.installEventFilter(self)
        
        self.lbl_monto_iva = QLabel("+$ 0,00")
        self.lbl_monto_iva.setStyleSheet("color: #64748B; font-size: 14px; font-weight: 600;")
        
        self.lbl_total = QLabel("$ 0,00")
        self.lbl_total.setStyleSheet("font-weight: 900; font-size: 24px; color: #2563EB; letter-spacing: -0.5px;")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # --- ACCIONES ---
        if self.is_edicion:
            texto_btn = "Guardar [F12]"
        else:
            texto_btn = "Crear Presupuesto [F12]" if self.is_presupuesto else "Confirmar Venta [F12]"
            
        self.btn_confirmar = QPushButton(texto_btn)
        self.btn_confirmar.setObjectName("btn_primario")
        self.btn_confirmar.setFixedHeight(36)
        self.btn_confirmar.setMinimumWidth(200)
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.clicked.connect(lambda: self.confirmar_operacion(self.tipo_documento_seleccionado))
        self.btn_confirmar.setStyleSheet("""
            QPushButton#btn_primario {
                background-color: #2563EB;
                color: #FFFFFF;
                border-radius: 6px;
                font-weight: 700;
                font-size: 15px;
                border: none;
            }
            QPushButton#btn_primario:hover {
                background-color: #1D4ED8;
            }
        """)

        # ESTRUCTURAR LAYOUT SEGUN OPERACION
        self.armar_panel_inferior(layout_footer)
            
        layout_principal.addWidget(self.contenedor_footer, stretch=0)

    def armar_panel_inferior(self, layout):
        pass

    # Las funciones _armar_footer_venta y _armar_footer_presupuesto fueron removidas.

    def _mostrar_ayuda(self):
        from ui.components.ayuda import DialogoAyudaContextual
        
        texto = (
            "<p><b>FUNCIONES PRINCIPALES:</b></p>"
            "<ul>"
            "<li><b>Buscar productos:</b> Utilizá el buscador principal (F2) por código, descripción corta o escaner.</li>"
            "<li><b>Sugerencias rápidas:</b> Al escribir, verás coincidencias inmediatas con su imagen en miniatura. Navegalas con las flechas del teclado y presioná Enter.</li>"
            "<li><b>Consultar Stock (ATP):</b> El buscador y el carrito indican el stock <em>disponible real</em> para la venta, evitando vender mercadería ya comprometida.</li>"
            "<li><b>Modificar el carrito:</b> Podés editar cantidades o aplicar descuentos por ítem haciendo doble clic o Enter sobre la celda correspondiente en la tabla.</li>"
            "<li><b>Seleccionar Cliente:</b> Buscá un cliente registrado (F3) o crealo rápidamente desde el panel de cliente final.</li>"
            "</ul>"
            "<p><b>DIFERENCIA ENTRE VENTA Y PRESUPUESTO:</b></p>"
            "<ul>"
            "<li>Una <b>Venta</b> genera un comprobante definitivo y extrae físicamente el producto del inventario.</li>"
            "<li>Un <b>Presupuesto</b> sólo genera un compromiso temporal del stock (reserva el ATP) sin tocar el físico, válido por 48 horas.</li>"
            "</ul>"
            "<p><b>ATAJOS DE TECLADO:</b></p>"
            "<ul>"
            "<li><b>F2:</b> Foco en el buscador de productos.</li>"
            "<li><b>F3:</b> Foco en el buscador de clientes.</li>"
            "<li><b>Flechas Arriba/Abajo:</b> Navegar la lista de sugerencias de productos.</li>"
            "<li><b>Enter:</b> Seleccionar un producto de la lista, o editar celdas en el carrito.</li>"
            "<li><b>Escape:</b> Cerrar las sugerencias o limpiar selección activa.</li>"
            "</ul>"
        )
        
        if getattr(self, 'is_presupuesto', False):
            titulo = "Ayuda: Nuevo Presupuesto"
        else:
            titulo = "Ayuda: Venta"
            
        dialogo = DialogoAyudaContextual(titulo, "Guía rápida para facturación y reservas", texto, self)
        dialogo.exec()

    def hideEvent(self, event):
        super().hideEvent(event)

    def mousePressEvent(self, event):
        if hasattr(self, 'frame_buscador'):
            pos_in_frame = self.frame_buscador.mapFrom(self, event.position().toPoint())
            if self.frame_buscador.rect().contains(pos_in_frame):
                self.input_buscador.setFocus()
                super().mousePressEvent(event)
                return

        if hasattr(self, 'panel_resultados') and self.panel_resultados.isVisible():
            self.panel_resultados.hide()
            if hasattr(self, 'input_buscador') and self.input_buscador.hasFocus():
                self.input_buscador.clearFocus()
        super().mousePressEvent(event)


    def modal_nuevo_cliente(self):
        formulario = DialogoFormularioCliente(self.conn, parent=self)
        if formulario.exec() == QDialog.DialogCode.Accepted and formulario.id_guardado is not None:
            id_nuevo = formulario.id_guardado
            try:
                # Actualizar el listado en memoria
                self.cargar_autocompletado_clientes()
                # Seleccionarlo
                det = qc.obtener_detalle_cliente(self.conn, id_nuevo)
                if det:
                    self.seleccionar_cliente({
                        'id': id_nuevo,
                        'nombre': det['nombre'],
                        'cuit': det['cuit_dni'],
                        'tel': det['telefono']
                    })
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error post-guardado: {e}")

    def cargar_autocompletado_clientes(self):
        try:
            from db.queries_ventas import obtener_clientes_activos_resumen
            filas = obtener_clientes_activos_resumen(self.conn)
            self.lista_clientes = []
            lista_nombres = []
            for row in filas:
                c = {'id': row[0], 'nombre': row[1] or "", 'cuit': row[2] or "", 'tel': row[3] or ""}
                self.lista_clientes.append(c)
                texto = f"{c['nombre']} | CUIT/DNI: {c['cuit'] if c['cuit'] else '-'}"
                lista_nombres.append(texto)
                
            self.completer_cliente = QCompleter(lista_nombres, self.input_cliente)
            self.completer_cliente.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.completer_cliente.setFilterMode(Qt.MatchFlag.MatchContains)
            self.completer_cliente.activated.connect(
                lambda _texto: QTimer.singleShot(0, self.procesar_input_cliente)
            )
            self.completer_cliente.popup().setStyleSheet("""
                QListView { 
                    background-color: #ffffff; 
                    color: #172033;
                    border: 1px solid #cbd5e1;
                    padding: 5px;
                }
            """)
            self.input_cliente.setCompleter(self.completer_cliente)
        except Exception as e:
            print(f"Error cargando clientes: {e}")

    def procesar_input_cliente(self):
        texto = self.input_cliente.text().strip()
        if not texto:
            return
            
        encontrado = None
        # Buscar por texto exacto de la lista enriquecida (Nombre | CUIT: ...)
        for c in self.lista_clientes:
            texto_comp = f"{c['nombre']} | CUIT/DNI: {c['cuit'] if c['cuit'] else '-'}"
            if texto == texto_comp or c['nombre'].lower() == texto.lower():
                encontrado = c
                break
                
        if encontrado:
            self.seleccionar_cliente(encontrado)
        else:
            QMessageBox.information(self, "No Encontrado", "Cliente no encontrado. Por favor utilice el botón '+ Nuevo' para crearlo.")
            self.input_cliente.selectAll()

    def seleccionar_cliente(self, cliente):
        self.cliente_seleccionado = cliente
        self.lbl_nombre_cliente.setText(f"<b>{cliente['nombre']}</b>")
        
        datos = []
        if cliente.get('cuit'): datos.append(f"CUIT/DNI: {cliente['cuit']}")
        if cliente.get('tel'): datos.append(f"Tel: {cliente['tel']}")
        self.lbl_datos_cliente.setText(" | ".join(datos) if datos else "Sin CUIT ni Tel")
        
        self.widget_busqueda_cliente.setVisible(False)
        self.widget_tarjeta_cliente.setVisible(True)
        self.input_buscador.setFocus()
        self._emitir_estado_cambiado()
        
    def deseleccionar_cliente(self):
        self.cliente_seleccionado = None
        self.input_cliente.clear()
        self.widget_tarjeta_cliente.setVisible(False)
        self.widget_busqueda_cliente.setVisible(True)
        self.input_cliente.setFocus()
        self._emitir_estado_cambiado()



    def cargar_catalogo_memoria(self):
        try:
            from db.queries_ventas import obtener_catalogo_venta
            filas = obtener_catalogo_venta(self.conn)
            
            # Agrupar por código
            mapa = {}
            for r in filas:
                cod = str(r[0])
                if cod not in mapa:
                    mapa[cod] = {
                        'codigo': cod,
                        'desc': str(r[1]),
                        'unidad_base': str(r[2]),
                        'stock': float(r[3] if r[3] is not None else 0.0),
                        'precio_base': float(r[4] if r[4] is not None else 0.0),
                        'imagen_path': r[8] if len(r) > 8 else None,
                        'unidades_venta': [
                            {'unidad': str(r[2]), 'factor': 1.0}
                        ]
                    }
                # Si hay conversión
                if r[5] is not None:
                    # Evitar duplicar la base si está en la tabla
                    if str(r[5]) != str(r[2]):
                        factor = float(r[6])
                        if factor <= 0:
                            continue
                        if (r[7] or 'MULTIPLICAR') == 'DIVIDIR':
                            factor = 1.0 / factor
                        mapa[cod]['unidades_venta'].append({
                            'unidad': str(r[5]),
                            'factor': factor
                        })
            
            self.catalogo = list(mapa.values())
        except Exception as e:
            print(f"Error cargando catálogo: {e}")
            self.catalogo = []

    def filtrar_productos(self, texto: str) -> list[dict]:
        texto = texto.strip().lower()
        if not texto:
            return []
            
        exactos = []
        empiezan_cod = []
        empiezan_desc = []
        contienen = []
        
        for p in self.catalogo:
            cod_low = p['codigo'].lower()
            desc_low = p['desc'].lower()
            
            if cod_low == texto:
                exactos.append(p)
            elif cod_low.startswith(texto):
                empiezan_cod.append(p)
            elif desc_low.startswith(texto):
                empiezan_desc.append(p)
            elif texto in cod_low or texto in desc_low:
                contienen.append(p)
                
        resultados = exactos + empiezan_cod + empiezan_desc + contienen
        # Eliminar duplicados si los hubiera (manteniendo orden)
        vistos = set()
        finales = []
        for r in resultados:
            if r['codigo'] not in vistos:
                vistos.add(r['codigo'])
                finales.append(r)
                if len(finales) >= 8:
                    break
        return finales

    def obtener_sugerencias_rapidas(self) -> list[dict]:
        # El catálogo ya está cargado y ordenado por la consulta SQL (ORDER BY p.descripcion)
        # Retornamos una copia o la misma lista para mostrar todo el catálogo.
        return self.catalogo

    def on_buscador_text_changed(self, texto):
        if not self._suspender_resultados and getattr(self, "producto_en_foco", None) is not None:
            self.producto_en_foco = None
            self.btn_limpiar_buscador.setVisible(False)
            self.input_cantidad.clear()
            self.input_cantidad.setEnabled(False)
            self.combo_unidad.setVisible(False)
            self.lbl_vender_por.setVisible(False)
            self.actualizar_etiqueta_cantidad()
            
        if self._suspender_resultados:
            self.panel_resultados.hide()
            return
            
        texto_busqueda = texto.strip()
        if not texto_busqueda:
            resultados = self.obtener_sugerencias_rapidas()
        else:
            resultados = self.filtrar_productos(texto_busqueda)
            
        self.lista_resultados.clear()
        
        if not resultados:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.DisplayRole, f"No se encontraron productos para '{texto}'")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.lista_resultados.addItem(item)
        else:
            from ui.components.image_selector import resolver_ruta_imagen
            from PyQt6.QtGui import QPixmap
            for p in resultados:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, p)
                
                img_path = resolver_ruta_imagen(p.get('imagen_path'))
                if img_path:
                    pix = QPixmap(str(img_path))
                    if not pix.isNull():
                        pix = pix.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                        item.setData(Qt.ItemDataRole.DecorationRole, pix)
                
                self.lista_resultados.addItem(item)
                
        self.mostrar_panel_resultados()

    def mostrar_panel_resultados(self):
        pos = self.input_buscador.mapToGlobal(self.input_buscador.rect().bottomLeft())
        pos.setY(pos.y() + 2)
        self.panel_resultados.move(pos)
        self.panel_resultados.setFixedWidth(self.input_buscador.width())
        
        h = 0
        for i in range(self.lista_resultados.count()):
            h += self.lista_resultados.sizeHintForRow(i)
        h = min(h + 4, 300)
        self.panel_resultados.setFixedHeight(h)
        
        self.panel_resultados.show()

    def eventFilter(self, obj, event):
        if obj == self.input_buscador and event.type() == QEvent.Type.KeyPress:
            if self.panel_resultados.isVisible():
                if event.key() in [Qt.Key.Key_Down, Qt.Key.Key_Up]:
                    count = self.lista_resultados.count()
                    if count > 0:
                        if not (self.lista_resultados.item(0).flags() & Qt.ItemFlag.ItemIsSelectable):
                            return super().eventFilter(obj, event)
                            
                        actual = self.lista_resultados.currentRow()
                        if event.key() == Qt.Key.Key_Down:
                            siguiente = (actual + 1) % count if actual >= 0 else 0
                        else:
                            siguiente = (actual - 1) % count if actual >= 0 else count - 1
                        self.lista_resultados.setCurrentRow(siguiente)
                    return True
                elif event.key() in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
                    texto_busqueda = self.input_buscador.text().strip()
                    if texto_busqueda:
                        resultados = self.filtrar_productos(texto_busqueda)
                        coincidencia = None
                        if len(resultados) == 1:
                            coincidencia = resultados[0]
                        elif len(resultados) > 1:
                            exactos = [p for p in resultados if p['codigo'].lower() == texto_busqueda.lower()]
                            if len(exactos) == 1:
                                coincidencia = exactos[0]
                        
                        if coincidencia:
                            self.seleccionar_producto(coincidencia)
                            if not self.input_cantidad.text():
                                self.input_cantidad.setText("1")
                            self.agregar_al_carrito()
                            return True

                    actual = self.lista_resultados.currentRow()
                    if actual < 0 and self.lista_resultados.count() > 0:
                        if self.lista_resultados.item(0).flags() & Qt.ItemFlag.ItemIsSelectable:
                            self.lista_resultados.setCurrentRow(0)
                            actual = 0
                    if actual >= 0:
                        self.on_resultado_clickeado(self.lista_resultados.item(actual))
                    return True
                elif event.key() == Qt.Key.Key_Escape:
                    self.panel_resultados.hide()
                    return True
            else:
                if event.key() in [Qt.Key.Key_Down, Qt.Key.Key_Enter, Qt.Key.Key_Return]:
                    if event.key() in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
                        texto_busqueda = self.input_buscador.text().strip()
                        if texto_busqueda:
                            resultados = self.filtrar_productos(texto_busqueda)
                            coincidencia = None
                            if len(resultados) == 1:
                                coincidencia = resultados[0]
                            elif len(resultados) > 1:
                                exactos = [p for p in resultados if p['codigo'].lower() == texto_busqueda.lower()]
                                if len(exactos) == 1:
                                    coincidencia = exactos[0]
                            
                            if coincidencia:
                                self.seleccionar_producto(coincidencia)
                                if not self.input_cantidad.text():
                                    self.input_cantidad.setText("1")
                                self.agregar_al_carrito()
                                return True
                    
                    self.on_buscador_text_changed(self.input_buscador.text())
                    return True
                    
        elif obj == self.input_buscador and event.type() == QEvent.Type.FocusIn:
            self.frame_buscador.setStyleSheet("""
                QFrame#frame_buscador {
                    background-color: #FFFFFF;
                    border: 1px solid #3B82F6;
                    border-radius: 6px;
                }
            """)
            # Mostrar sugerencias automáticamente si está vacío o tiene texto y no hay producto seleccionado
            if getattr(self, "producto_en_foco", None) is None:
                QTimer.singleShot(0, lambda: self.on_buscador_text_changed(self.input_buscador.text()))
                    
        elif obj == getattr(self, "combo_unidad", None) and event.type() == QEvent.Type.KeyPress:
            if event.key() in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
                self.input_cantidad.setFocus()
                return True
                
        if obj == self.input_buscador and event.type() == QEvent.Type.FocusOut:
            self.frame_buscador.setStyleSheet("""
                QFrame#frame_buscador {
                    background-color: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                }
            """)
            QTimer.singleShot(100, self.chequear_foco_panel)
            
        if event.type() == QEvent.Type.FocusIn and obj in (getattr(self, 'input_desc_gral', None), getattr(self, 'input_iva_porc', None), getattr(self, 'input_cantidad', None)):
            QTimer.singleShot(0, obj.selectAll)
            
        return super().eventFilter(obj, event)

    def chequear_foco_panel(self):
        if not self.input_buscador.hasFocus() and not self.panel_resultados.hasFocus() and not self.lista_resultados.hasFocus():
            self.panel_resultados.hide()

    def on_resultado_clickeado(self, item):
        producto = item.data(Qt.ItemDataRole.UserRole)
        if producto:
            self.seleccionar_producto(producto)

    def limpiar_buscador_producto(self):
        self.producto_en_foco = None
        self.btn_limpiar_buscador.setVisible(False)
        self.input_cantidad.clear()
        self.input_cantidad.setEnabled(False)
        self.combo_unidad.setVisible(False)
        self.lbl_vender_por.setVisible(False)
        self.actualizar_etiqueta_cantidad()
        self.input_buscador.clear()
        self.input_buscador.setFocus()

    def seleccionar_producto(self, producto: dict):
        self.producto_en_foco = producto.copy()
        self.panel_resultados.hide()
        
        self._suspender_resultados = True
        self.input_buscador.setText(f"{producto['codigo']} - {producto['desc']}")
        self._suspender_resultados = False
        self.btn_limpiar_buscador.setVisible(True)
        
        unidades = producto['unidades_venta']
        if len(unidades) > 1:
            self.combo_unidad.clear()
            for u in unidades:
                self.combo_unidad.addItem(u['unidad'], u['factor'])
            
            idx_base = 0
            for i, u in enumerate(unidades):
                if u['unidad'] == producto['unidad_base']:
                    idx_base = i
                    break
            self.combo_unidad.setCurrentIndex(idx_base)
            
            self.lbl_vender_por.setVisible(True)
            self.combo_unidad.setVisible(True)
            self.combo_unidad.setFocus()
        else:
            self.combo_unidad.clear()
            self.combo_unidad.addItem(unidades[0]['unidad'], unidades[0]['factor'])
            self.lbl_vender_por.setVisible(False)
            self.combo_unidad.setVisible(False)
            self.input_cantidad.setEnabled(True)
            self.input_cantidad.setFocus()
            self.input_cantidad.setText("1")
            self.input_cantidad.selectAll()
            
        self.actualizar_etiqueta_cantidad()
            
    def on_unidad_cambiada(self, index):
        if index >= 0:
            self.input_cantidad.setEnabled(True)
            self.input_cantidad.setText("1")
            self.actualizar_etiqueta_cantidad()

    def actualizar_etiqueta_cantidad(self):
        if not getattr(self, "producto_en_foco", None):
            self.lbl_cant.setText("CANTIDAD")
            return
            
        unidad = self.combo_unidad.currentText()
        if unidad == "m2":
            self.lbl_cant.setText("CANTIDAD M²")
        elif unidad == "u":
            self.lbl_cant.setText("CANTIDAD UNIDAD")
        else:
            self.lbl_cant.setText("CANTIDAD")

    def calcular_precio_por_unidad_venta(self, precio_base: float, factor: float) -> float:
        return precio_base * factor

    def requiere_control_stock(self):
        return not self.is_presupuesto

    def cantidad_base_en_carrito(self, codigo, excluir_fila=None):
        total = 0.0
        for indice, item in enumerate(self.carrito):
            if indice != excluir_fila and item['codigo'] == codigo:
                total += item['cantidad'] * item['factor_conversion']
        return total

    def stock_restante_para_linea(self, producto, excluir_fila=None):
        return producto['stock'] - self.cantidad_base_en_carrito(
            producto['codigo'], excluir_fila
        )

    def configurar_atajos(self):
        QShortcut(QKeySequence("F2"), self).activated.connect(self.enfocar_buscador)
        QShortcut(QKeySequence("F3"), self).activated.connect(self.enfocar_cliente)
        QShortcut(QKeySequence("F11"), self).activated.connect(self.vaciar_carrito_directo)
        QShortcut(QKeySequence("F12"), self).activated.connect(lambda: self.confirmar_operacion(self.tipo_documento_seleccionado))
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.intentar_vaciar_carrito)
        self.atajo_borrar = QShortcut(QKeySequence("Delete"), self.tabla)
        self.atajo_borrar.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.atajo_borrar.activated.connect(self.borrar_fila_seleccionada)
        self.atajo_retroceso = QShortcut(QKeySequence("Backspace"), self.tabla)
        self.atajo_retroceso.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.atajo_retroceso.activated.connect(self.borrar_fila_seleccionada)
        self.atajo_duplicar = QShortcut(QKeySequence("Ctrl+D"), self.tabla)
        self.atajo_duplicar.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.atajo_duplicar.activated.connect(self.duplicar_fila_seleccionada)

    def enfocar_buscador(self):
        self.input_buscador.setFocus()
        self.input_buscador.selectAll()
        
    def enfocar_cliente(self):
        if self.widget_busqueda_cliente.isVisible():
            self.input_cliente.setFocus()
            self.input_cliente.selectAll()

    # --- LÓGICA DE NEGOCIO ---

    def agregar_al_carrito(self):
        if not self.producto_en_foco: 
            return
            
        texto_cant = self.input_cantidad.text()
        cantidad_ingresada = parsear_arg(texto_cant)
        
        if cantidad_ingresada <= 0:
            QMessageBox.warning(self, "Error de Cantidad", "La cantidad debe ser un número mayor a cero.")
            self.input_cantidad.selectAll()
            return
            
        unidad_venta = self.combo_unidad.currentText()
        factor_conversion = float(self.combo_unidad.currentData())
        
        cantidad_base = cantidad_ingresada * factor_conversion

        uv_lower = unidad_venta.lower()
        if uv_lower in ['u', 'unidad', 'unidades'] and not cantidad_ingresada.is_integer():
            QMessageBox.warning(self, "Unidad Restringida", f"Este producto se vende por {unidad_venta} entera.\nNo se aceptan decimales en esta unidad.")
            self.input_cantidad.selectAll()
            return

        stock_restante = self.stock_restante_para_linea(self.producto_en_foco)
        if self.requiere_control_stock() and cantidad_base > stock_restante:
            QMessageBox.critical(self, "Stock Insuficiente", 
                f"No hay stock suficiente.\nDisponibles para esta operación: {stock_restante:g} {self.producto_en_foco['unidad_base']}\n"
                f"Equivale a lo requerido: {cantidad_base:g} {self.producto_en_foco['unidad_base']}\n"
                f"Producto: {self.producto_en_foco['desc']}")
            self.input_cantidad.selectAll()
            return

        precio_unit_mostrado = self.calcular_precio_por_unidad_venta(self.producto_en_foco['precio_base'], factor_conversion)

        self.insertar_fila(self.producto_en_foco, unidad_venta, factor_conversion, cantidad_ingresada, cantidad_base, precio_unit_mostrado)
        
        self.producto_en_foco = None
        self.btn_limpiar_buscador.setVisible(False)
        self.input_cantidad.clear()
        self.input_cantidad.setEnabled(False)
        self.combo_unidad.setVisible(False)
        self.lbl_vender_por.setVisible(False)
        self.input_buscador.clear()
        self.input_buscador.setFocus()
        self.actualizar_etiqueta_cantidad()
        self.mostrar_feedback_temporal(f"✓ Añadido al carrito", "success")

    def mostrar_feedback_temporal(self, mensaje, tipo="success"):
        self._feedback_activo = True
        if tipo == "success":
            self.lbl_info_items.setStyleSheet("color: #047857; font-weight: 600; font-size: 14px; padding: 6px 12px; background: #D1FAE5; border-radius: 16px;")
        elif tipo == "warning":
            self.lbl_info_items.setStyleSheet("color: #B45309; font-weight: 600; font-size: 14px; padding: 6px 12px; background: #FEF3C7; border-radius: 16px;")
        else:
            self.lbl_info_items.setStyleSheet("color: #0F172A; font-weight: 600; font-size: 14px; padding: 6px 12px; background: #F1F5F9; border-radius: 16px;")
            
        self.lbl_info_items.setText(mensaje)
        
        if hasattr(self, '_feedback_timer'):
            self._feedback_timer.stop()
        else:
            self._feedback_timer = QTimer(self)
            self._feedback_timer.setSingleShot(True)
            self._feedback_timer.timeout.connect(self.restaurar_feedback)
            
        self._feedback_timer.start(2000)

    def restaurar_feedback(self):
        self._feedback_activo = False
        self.actualizar_totales()

    def insertar_fila(self, prod, unidad_venta, factor_conversion, cantidad, cantidad_base, precio_unit_mostrado):
        self.tabla.blockSignals(True)
        
        row = self.tabla.rowCount()
        self.tabla.insertRow(row)
        
        i_cod = QTableWidgetItem(prod['codigo'])
        i_desc = QTableWidgetItem(prod['desc'])
        
        i_unidad = QTableWidgetItem(unidad_venta)
        i_unidad.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        font_editable = QFont()
        font_editable.setBold(True)
        
        i_cant = QTableWidgetItem(f"{cantidad:g}")
        i_cant.setForeground(QColor("#2563EB"))
        i_cant.setBackground(QColor("#F8FAFC"))
        i_cant.setFont(font_editable)
        i_cant.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        i_cant.setToolTip(f"Doble clic o Enter para editar.\nStock disponible: {prod['stock']:g} {prod['unidad_base']}")
        
        str_equiv = f"{cantidad_base:g} {prod['unidad_base']}"
        i_equiv = QTableWidgetItem(str_equiv)
        if factor_conversion == 1.0:
            i_equiv.setForeground(QColor("#94A3B8"))
        i_equiv.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        i_precio = QTableWidgetItem(f"$ {formato_arg(precio_unit_mostrado)}")
        i_precio.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        i_desc_val = QTableWidgetItem("0")
        i_desc_val.setForeground(QColor("#2563EB"))
        i_desc_val.setBackground(QColor("#F8FAFC"))
        i_desc_val.setFont(font_editable)
        i_desc_val.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        i_desc_val.setToolTip("Doble clic o Enter para editar descuento.")
        
        subtotal = cantidad * precio_unit_mostrado
        i_sub = QTableWidgetItem(f"$ {formato_arg(subtotal)}")
        i_sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        font_sub = QFont()
        font_sub.setBold(True)
        i_sub.setFont(font_sub)
        
        from ui.components.boton_x import BotonCerrarX
        btn_borrar = BotonCerrarX()
        btn_borrar.setObjectName("btn_borrar")
        btn_borrar.setFixedSize(24, 24)
        btn_borrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_borrar.setToolTip("Eliminar producto (Del/Backspace)")
        btn_borrar.clicked.connect(lambda _, r=row: self.borrar_fila_por_boton(r))
        
        w_borrar = QWidget()
        ly_borrar = QHBoxLayout(w_borrar)
        ly_borrar.setContentsMargins(0, 0, 0, 0)
        ly_borrar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ly_borrar.addWidget(btn_borrar)
        
        for item in (i_cod, i_desc, i_unidad, i_equiv, i_precio, i_sub):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
        self.tabla.setItem(row, 0, i_cod)
        self.tabla.setItem(row, 1, i_desc)
        self.tabla.setItem(row, 2, i_unidad)
        self.tabla.setItem(row, 3, i_cant)
        self.tabla.setItem(row, 4, i_equiv)
        self.tabla.setItem(row, 5, i_precio)
        self.tabla.setItem(row, 6, i_desc_val)
        self.tabla.setItem(row, 7, i_sub)
        self.tabla.setCellWidget(row, 8, w_borrar)
        
        self.carrito.append({
            'codigo': prod['codigo'], 
            'desc_prod': prod['desc'],
            'unidad_base': prod['unidad_base'],
            'unidad_venta': unidad_venta,
            'factor_conversion': factor_conversion,
            'stock': prod['stock'], 
            'precio_base': prod['precio_base'],
            'precio_unit_mostrado': precio_unit_mostrado,
            'cantidad': cantidad,
            'descuento': 0.0
        })
        
        self.actualizar_totales()
        self.tabla.blockSignals(False)

    def celda_editada(self, item):
        col = item.column()
        row = item.row()
        
        if col not in [3, 6]: 
            return
            
        prod = self.carrito[row]
        valor = parsear_arg(item.text())

        self.tabla.blockSignals(True)
        
        if col == 3: # Cantidad
            uv_lower = prod['unidad_venta'].lower()
            if uv_lower in ['u', 'unidad', 'unidades'] and not valor.is_integer():
                QMessageBox.warning(self, "Unidad Inválida", "Producto sin decimales permitidos en esta unidad.")
                valor = prod['cantidad']
            else:
                nueva_cant_base = valor * prod['factor_conversion']
                stock_restante = self.stock_restante_para_linea(prod, excluir_fila=row)
                if self.requiere_control_stock() and nueva_cant_base > stock_restante:
                    QMessageBox.warning(self, "Stock Excedido", f"Solo hay {stock_restante:g} {prod['unidad_base']} disponibles para esta operación.")
                    valor = prod['cantidad']
                elif valor <= 0:
                    QMessageBox.warning(self, "Cantidad Inválida", "La cantidad debe ser mayor a 0.")
                    valor = prod['cantidad']
                else:
                    prod['cantidad'] = valor
                    
            item.setText(f"{valor:g}")
            
            cant_base = prod['cantidad'] * prod['factor_conversion']
            self.tabla.item(row, 4).setText(f"{cant_base:g} {prod['unidad_base']}")
            
        elif col == 6: # Descuento (%)
            if valor < 0 or valor > 100:
                QMessageBox.warning(self, "Rango Inválido", "El descuento debe estar entre 0% y 100%.")
                valor = prod['descuento']
            else:
                prod['descuento'] = valor
                
            item.setText(f"{valor:g}")
            
        subtotal = prod['cantidad'] * prod['precio_unit_mostrado'] * (1 - (prod['descuento'] / 100.0))
        self.tabla.item(row, 7).setText(f"$ {formato_arg(subtotal)}")
        
        self.tabla.blockSignals(False)
        self.actualizar_totales()

    def borrar_fila_por_boton(self, row):
        btn = self.sender()
        if btn:
            idx = self.tabla.indexAt(btn.pos())
            if idx.isValid():
                r = idx.row()
                self.tabla.removeRow(r)
                del self.carrito[r]
                self.actualizar_totales()
                self.mostrar_feedback_temporal("✕ Producto eliminado", "warning")

    def borrar_fila_seleccionada(self):
        filas = set([item.row() for item in self.tabla.selectedItems()])
        if not filas: 
            return
        for fila in sorted(filas, reverse=True):
            self.tabla.removeRow(fila)
            del self.carrito[fila]
        self.actualizar_totales()
        self.mostrar_feedback_temporal("✕ Productos eliminados", "warning")

    def duplicar_fila_seleccionada(self):
        filas = set([item.row() for item in self.tabla.selectedItems()])
        if not filas: 
            return
        
        for fila in sorted(filas):
            prod = self.carrito[fila]
            
            prod_base = {
                'codigo': prod['codigo'],
                'desc': prod['desc_prod'],
                'unidad_base': prod['unidad_base'],
                'stock': prod['stock'],
                'precio_base': prod['precio_base']
            }
            
            self.insertar_fila(
                prod=prod_base, 
                unidad_venta=prod['unidad_venta'], 
                factor_conversion=prod['factor_conversion'], 
                cantidad=prod['cantidad'], 
                cantidad_base=prod['cantidad'] * prod['factor_conversion'], 
                precio_unit_mostrado=prod['precio_unit_mostrado']
            )
            
            ultima_fila = self.tabla.rowCount() - 1
            if prod['descuento'] > 0:
                self.tabla.item(ultima_fila, 6).setText(f"{prod['descuento']:g}")

    def intentar_vaciar_carrito(self):
        if self.panel_resultados.isVisible():
            self.panel_resultados.hide()
            return
            
        if self.input_cantidad.isEnabled():
            self.input_cantidad.clear()
            self.input_cantidad.setEnabled(False)
            self.combo_unidad.setVisible(False)
            self.lbl_vender_por.setVisible(False)
            self.producto_en_foco = None
            self.input_buscador.setFocus()
            return
            
        if self.input_buscador.text():
            self.input_buscador.clear()
            return
            
        self.vaciar_carrito_directo()

    def vaciar_carrito_directo(self):
        if self.carrito:
            resp = QMessageBox.warning(self, "Limpiar Venta", 
                                       f"¿Borrar los {len(self.carrito)} productos actuales y reiniciar?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp == QMessageBox.StandardButton.Yes:
                self.tabla.setRowCount(0)
                self.carrito.clear()
                self.descuento_general = 0.0
                self.input_desc_gral.setText("0")
                self.chk_iva.setChecked(False)
                self.input_iva_porc.setText("21")
                self.iva_porcentaje = 21.0
                self.iva_aplicado = False
                self.actualizar_totales()
                self.deseleccionar_cliente()
                self.input_observaciones.clear()
                self.input_buscador.setFocus()
                self.mostrar_feedback_temporal("⚪ Carrito vacío", "normal")

    def on_descuento_general_editado(self):
        valor = parsear_arg(self.input_desc_gral.text())
        if valor < 0 or valor > 100:
            QMessageBox.warning(self, "Rango Inválido", "El descuento general debe estar entre 0% y 100%.")
            self.input_desc_gral.setText(f"{self.descuento_general:g}")
        else:
            self.descuento_general = valor
            self.input_desc_gral.setText(f"{valor:g}")
            self.actualizar_totales()

    def on_iva_toggled(self, state):
        self.iva_aplicado = (state == Qt.CheckState.Checked.value)
        self.input_iva_porc.setEnabled(self.iva_aplicado)
        self.actualizar_totales()

    def on_iva_editado(self):
        valor = parsear_arg(self.input_iva_porc.text())
        if valor < 0 or valor > 100:
            QMessageBox.warning(self, "Rango Inválido", "El IVA debe estar entre 0% y 100%.")
            self.input_iva_porc.setText(f"{self.iva_porcentaje:g}")
        else:
            self.iva_porcentaje = valor
            self.input_iva_porc.setText(f"{valor:g}")
            self.actualizar_totales()

    def actualizar_totales(self):
        subtotal_bruto = 0.0
        unidades_totales = 0.0
        
        for p in self.carrito:
            subtotal_fila = p['cantidad'] * p['precio_unit_mostrado'] * (1 - (p['descuento'] / 100.0))
            subtotal_bruto += subtotal_fila
            unidades_totales += p['cantidad']
            
        monto_desc_gral = subtotal_bruto * (self.descuento_general / 100.0)
        subtotal_neto = subtotal_bruto - monto_desc_gral
        
        monto_iva = subtotal_neto * (self.iva_porcentaje / 100.0) if self.iva_aplicado else 0.0
        self.total_final_calculado = subtotal_neto + monto_iva # guardamos para poder emitirlo
            
        self.lbl_subtotal.setText(f"$ {formato_arg(subtotal_bruto)}")
        self.lbl_monto_desc.setText(f"-$ {formato_arg(monto_desc_gral)}")
        self.lbl_monto_iva.setText(f"+$ {formato_arg(monto_iva)}")
        self.lbl_total.setText(f"$ {formato_arg(self.total_final_calculado)}")
        
        estado = "🟢 Nueva operación" if not self.carrito else "🟢 En curso"
        
        # Actualizar labels dependientes
        if not getattr(self, '_feedback_activo', False):
            self.lbl_info_items.setStyleSheet("color: #0F172A; font-weight: 600; font-size: 14px; padding: 6px 12px; background: #F1F5F9; border-radius: 16px;")
            self.lbl_info_items.setText(estado)
            
        self.lbl_resumen_rapido.setText(f"{len(self.carrito)} productos · {unidades_totales:g} unidades")
        
        # Actualizar estado vacío
        if not self.carrito:
            self.stack_tabla.setCurrentIndex(0)
        else:
            self.stack_tabla.setCurrentIndex(1)
            
        self._emitir_estado_cambiado()

    def _emitir_estado_cambiado(self):
        total = getattr(self, 'total_final_calculado', 0.0)
        self.estado_cambiado.emit({
            'tipo': self.tipo_documento_seleccionado,
            'cliente': self.cliente_seleccionado,
            'items': len(self.carrito),
            'total': total,
            'is_edicion': self.is_edicion,
            'id_presupuesto_edicion': getattr(self, 'id_presupuesto_edicion', None)
        })

    def esta_vacia(self):
        return len(self.carrito) == 0 and self.cliente_seleccionado is None

    def confirmar_operacion(self, tipo):
        self.setFocus()
        if not self.carrito: 
            QMessageBox.information(self, "Venta Vacía", "Agrega al menos un producto para confirmar.")
            return
            
        descontar_stock = not self.is_presupuesto
        if tipo == 'PRESUPUESTO':
            descontar_stock = False
        
        try:
            id_cliente_final = self.cliente_seleccionado['id'] if self.cliente_seleccionado else None
            obs = self.input_observaciones.text().strip()
            
            # Recopilar datos reales para el comprobante antes de limpiar
            fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
            nombre_cliente = self.cliente_seleccionado['nombre'] if self.cliente_seleccionado else "Consumidor Final"
            cuit_cliente = self.cliente_seleccionado.get('documento', '') if self.cliente_seleccionado else ""
            if cuit_cliente:
                cliente_txt = f"{nombre_cliente} ({cuit_cliente})"
            else:
                cliente_txt = nombre_cliente
                
            cant_prods = len(self.carrito)
            unidades_totales = sum(item['cantidad'] for item in self.carrito)
            total_final_str = self.lbl_total.text()
            desconto_stock_str = "Sí" if descontar_stock else "No"
            
            if self.is_edicion and self.id_presupuesto_edicion:
                from db.queries_presupuestos import editar_presupuesto_activo
                numero_interno = editar_presupuesto_activo(
                    self.conn, self.id_presupuesto_edicion, self.carrito,
                    self.descuento_general, self.iva_aplicado, self.iva_porcentaje,
                    id_cliente_final, obs
                )
                id_doc = self.id_presupuesto_edicion
                msg = f"Presupuesto #{numero_interno} editado con éxito."
            else:
                from db.queries_ventas import registrar_operacion_venta
                id_doc, numero_interno, msg = registrar_operacion_venta(
                    self.conn, tipo, descontar_stock, self.carrito,
                    self.descuento_general, self.iva_aplicado, self.iva_porcentaje,
                    id_cliente_final, obs
                )
            
            modal_exito = DialogoVentaExitosa(
                conn=self.conn,
                id_documento=id_doc,
                num_venta=numero_interno,
                cliente_txt=cliente_txt,
                fecha_hora=fecha_hora,
                cant_prods=cant_prods,
                cant_unidades=unidades_totales,
                total=total_final_str,
                desconto_stock=desconto_stock_str,
                is_presupuesto=self.is_presupuesto,
                parent=self
            )
            modal_exito.exec()
            
            # Reset Total
            self.tabla.setRowCount(0)
            self.carrito.clear()
            self.descuento_general = 0.0
            self.input_desc_gral.setText("0")
            self.chk_iva.setChecked(False)
            self.input_iva_porc.setText("21")
            self.iva_porcentaje = 21.0
            self.iva_aplicado = False
            self.actualizar_totales()
            self.deseleccionar_cliente()
            self.input_observaciones.clear()
            self.input_buscador.setFocus()
            
            if self.is_edicion:
                self.is_edicion = False
                self.id_presupuesto_edicion = None
                if hasattr(self, 'btn_confirmar'):
                    self.btn_confirmar.setText("Crear Presupuesto [F12]" if self.is_presupuesto else "Confirmar Venta [F12]")
            
            self.cargar_catalogo_memoria()
            
            self.operacion_completada.emit(numero_interno)
            
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Error Transaccional", f"Hubo un error al procesar la operación:\n{e}")
