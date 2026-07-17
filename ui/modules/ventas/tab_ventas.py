from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QLabel, QPushButton, 
                             QHeaderView, QAbstractItemView, QMessageBox, QCheckBox,
                             QComboBox, QFrame, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
                             QDialog, QFormLayout, QButtonGroup, QCompleter, QSplitter,
                             QSplitterHandle, QStyledItemDelegate, QStackedWidget, QSizePolicy)
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
        <div style="color: {text_color};">
            <div style="font-size: 13px;"><b>{p['codigo']}</b> &nbsp; {p['desc']}</div>
            <div style="font-size: 11px; margin-top: 2px;">
                Stock Disp: <span style="color: {color_stock}; font-weight: bold;">{stock:g}</span> {p['unidad_base']} &nbsp;&middot;&nbsp; <b>$ {formato_arg(p['precio_base'])}</b>
            </div>
        </div>
        """
        
        doc = QTextDocument()
        doc.setDefaultFont(painter.font())
        doc.setDocumentMargin(0)
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
        resumen_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;")
        res_layout = QFormLayout(resumen_frame)
        res_layout.setContentsMargins(16, 16, 16, 16)
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
        self.btn_cerrar.setFixedHeight(40)
        self.btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar.clicked.connect(self.accept)
        
        self.btn_preview = QPushButton("Vista Previa")
        self.btn_preview.setObjectName("btn_secundario")
        self.btn_preview.setFixedHeight(40)
        self.btn_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_preview.clicked.connect(self._vista_previa_pdf)
        
        self.btn_pdf = QPushButton("Generar PDF")
        self.btn_pdf.setObjectName("btn_primario")
        self.btn_pdf.setFixedHeight(40)
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
            dlg = DialogoVistaPreviaPDF(tmp_path, self.parent())
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


class PestanaNuevaVenta(QWidget):
    operacion_completada = pyqtSignal(str)
    
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
        
        # Productos
        for d in det['detalles']:
            codigo = d['codigo_producto']
            
            # Buscar info base del catálogo en memoria
            prod_base = None
            for p in self.catalogo:
                if p['codigo'] == codigo:
                    prod_base = p
                    break
            
            if not prod_base: continue
            
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
                border: 1px solid #E4E7EC;
                border-radius: 12px;
            }
            QPushButton#btn_tipo_doc {
                background-color: #F4F7FB;
                color: #667085;
                border: 1px solid #E4E7EC;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton#btn_tipo_doc:checked {
                background-color: #2563EB;
                color: #FFFFFF;
                border-color: #2563EB;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #E4E7EC;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: #FFFFFF;
                selection-background-color: #2563EB;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #2563EB;
            }
            QPushButton#btn_primario {
                background-color: #2563EB;
                color: #FFFFFF;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                border: none;
            }
            QPushButton#btn_primario:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btn_secundario {
                background-color: #FFFFFF;
                color: #172033;
                border: 1px solid #E4E7EC;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton#btn_secundario:hover {
                background-color: #F4F7FB;
            }
            QPushButton#btn_peligro_sutil {
                color: #DC2626;
                background-color: transparent;
                border: none;
                font-weight: 600;
                font-size: 13px;
                padding: 4px;
            }
            QPushButton#btn_peligro_sutil:hover {
                text-decoration: underline;
            }

            QCheckBox { 
                font-size: 14px; 
                color: #172033; 
                font-weight: 500;
            }
            QCheckBox::indicator { 
                width: 18px; 
                height: 18px; 
                border: 2px solid #E4E7EC;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #2563EB;
                border-color: #2563EB;
                image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+");
            }
            QTableWidget {
                border: none;
                gridline-color: transparent;
                background-color: #FFFFFF;
                outline: none;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #64748B;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-bottom: 1px solid #E4E7EC;
                padding: 12px 8px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #F1F5F9;
                padding: 4px 8px;
                color: #172033;
            }
            QTableWidget::item:selected {
                background-color: #EBF5FF;
                color: #172033;
            }
        """)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(28, 28, 28, 28)
        layout_principal.setSpacing(20)

        # --- HEADER PRINCIPAL Y CLIENTE COMPACTO ---
        self.contenedor_header = QFrame()
        self.contenedor_header.setObjectName("tarjeta_blanca")
        layout_top = QHBoxLayout(self.contenedor_header)
        layout_top.setContentsMargins(20, 12, 20, 12)
        layout_top.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # Título de la pantalla
        tit_txt = "Nuevo Presupuesto" if self.is_presupuesto else "Venta"
        sub_txt = "Creación de nuevo presupuesto (Validez 48h)" if self.is_presupuesto else "Venta directa y gestión rápida de productos"
        ico_txt = "📄" if self.is_presupuesto else "🛒"
        
        from ui.components.encabezado import crear_encabezado_estandar
        ly_izq, btn_ayuda = crear_encabezado_estandar(ico_txt, tit_txt, sub_txt)
        btn_ayuda.clicked.connect(self._mostrar_ayuda)
        
        divisor = QFrame()
        divisor.setFrameShape(QFrame.Shape.VLine)
        divisor.setStyleSheet("color: #E4E7EC; margin-left: 12px; margin-right: 12px;")
        
        # 1. Buscador / Tarjeta Cliente (LADO IZQUIERDO - FRANJA COMPACTA)
        col_izq = QHBoxLayout()
        col_izq.setSpacing(8)
        col_izq.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        lbl_cli_tit = QLabel("Cliente:")
        lbl_cli_tit.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 600;")
        
        self.widget_busqueda_cliente = QWidget()
        self.widget_busqueda_cliente.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        layout_busq_cli = QHBoxLayout(self.widget_busqueda_cliente)
        layout_busq_cli.setContentsMargins(0, 0, 0, 0)
        layout_busq_cli.setSpacing(8)
        
        self.input_cliente = QLineEdit()
        self.input_cliente.setPlaceholderText("Buscar por nombre o CUIT (F3)...")
        self.input_cliente.setMinimumWidth(300)
        self.input_cliente.setMaximumWidth(450)
        self.input_cliente.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_cliente.returnPressed.connect(self.procesar_input_cliente)
        
        self.btn_nuevo_cliente = QPushButton("+ Nuevo")
        self.btn_nuevo_cliente.setObjectName("btn_secundario")
        self.btn_nuevo_cliente.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.btn_nuevo_cliente.setFixedWidth(80)
        self.btn_nuevo_cliente.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo_cliente.clicked.connect(self.modal_nuevo_cliente)
        
        layout_busq_cli.addWidget(self.input_cliente)
        layout_busq_cli.addWidget(self.btn_nuevo_cliente)
        
        self.widget_tarjeta_cliente = QFrame()
        self.widget_tarjeta_cliente.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E4E7EC; border-radius: 6px;")
        self.widget_tarjeta_cliente.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.widget_tarjeta_cliente.setMaximumWidth(450)
        layout_tarjeta_cli = QHBoxLayout(self.widget_tarjeta_cliente)
        layout_tarjeta_cli.setContentsMargins(12, 4, 8, 4)
        layout_tarjeta_cli.setSpacing(12)
        
        self.lbl_nombre_cliente = QLabel("<b>Nombre Cliente</b>")
        self.lbl_nombre_cliente.setStyleSheet("color: #1e293b; font-size: 13px;")
        self.lbl_datos_cliente = QLabel("CUIT/DNI - Tel")
        self.lbl_datos_cliente.setStyleSheet("color: #64748b; font-size: 12px;")
        
        from ui.components.boton_x import BotonCerrarX
        self.btn_quitar_cliente = BotonCerrarX()
        self.btn_quitar_cliente.setObjectName("btn_quitar_cliente")
        self.btn_quitar_cliente.clicked.connect(self.deseleccionar_cliente)
        
        layout_tarjeta_cli.addWidget(self.lbl_nombre_cliente)
        layout_tarjeta_cli.addWidget(self.lbl_datos_cliente)
        layout_tarjeta_cli.addWidget(self.btn_quitar_cliente)
        self.widget_tarjeta_cliente.setVisible(False)
        
        col_izq.addWidget(lbl_cli_tit)
        col_izq.addWidget(self.widget_busqueda_cliente)
        col_izq.addWidget(self.widget_tarjeta_cliente)
        
        col_izq.addWidget(btn_ayuda)
        
        # 3. Info y Estado (LADO DERECHO)
        self.lbl_info_items = QLabel("🟢 Nueva operación")
        self.lbl_info_items.setStyleSheet("color: #172033; font-weight: 600; font-size: 14px;")
        
        self.btn_vaciar_carrito = QPushButton("Vaciar carrito [F11]")
        self.btn_vaciar_carrito.setObjectName("btn_peligro_sutil")
        self.btn_vaciar_carrito.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_vaciar_carrito.clicked.connect(self.vaciar_carrito_directo)
        
        col_der = QVBoxLayout()
        col_der.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        col_der.addWidget(self.lbl_info_items, alignment=Qt.AlignmentFlag.AlignRight)
        col_der.addWidget(self.btn_vaciar_carrito, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_top.addLayout(ly_izq)
        layout_top.addWidget(divisor)
        layout_top.addLayout(col_izq)
        layout_top.addStretch()
        layout_top.addLayout(col_der)
        
        layout_principal.addWidget(self.contenedor_header, stretch=0)

        # --- ZONA CENTRAL: BUSCADOR + CARRITO ---
        self.contenedor_tabla = QFrame()
        self.contenedor_tabla.setObjectName("tarjeta_blanca")
        layout_tabla = QVBoxLayout(self.contenedor_tabla)
        layout_tabla.setContentsMargins(16, 16, 16, 16)
        layout_tabla.setSpacing(12)
        
        # 1. Buscador y Cantidad
        layout_buscador = QHBoxLayout()
        layout_buscador.setContentsMargins(0, 0, 0, 0)
        layout_buscador.setSpacing(12)
        
        self.input_buscador = QLineEdit()
        self.input_buscador.setPlaceholderText("🔍 Buscar producto por código o descripción... (F2)")
        self.input_buscador.setObjectName("input_buscador")
        self.input_buscador.setMinimumHeight(48)
        self.input_buscador.setStyleSheet("""
            QLineEdit {
                background-color: #F8FAFC;
                border: 1px solid #E4E7EC;
                border-radius: 8px;
                font-size: 16px;
                padding-left: 12px;
                color: #172033;
            }
            QLineEdit:focus {
                border: 1px solid #2563EB;
                background-color: #FFFFFF;
            }
        """)
        self.input_buscador.textChanged.connect(self.on_buscador_text_changed)
        self.input_buscador.installEventFilter(self)
        
        self.combo_unidad = QComboBox()
        self.combo_unidad.setFixedWidth(120)
        self.combo_unidad.setMinimumHeight(48)
        self.combo_unidad.setVisible(False)
        self.combo_unidad.installEventFilter(self)
        self.combo_unidad.currentIndexChanged.connect(self.on_unidad_cambiada)
        
        self.caja_cant_frame = QFrame()
        self.caja_cant_frame.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E4E7EC;
                border-radius: 8px;
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
        """)
        caja_cant = QHBoxLayout(self.caja_cant_frame)
        caja_cant.setContentsMargins(12, 6, 12, 6)
        caja_cant.setSpacing(12)
        
        self.lbl_cant = QLabel("CANT:")
        self.lbl_cant.setStyleSheet("color: #64748B; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        
        self.input_cantidad = QLineEdit()
        self.input_cantidad.setPlaceholderText("0")
        self.input_cantidad.setFixedWidth(60)
        self.input_cantidad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_cantidad.setObjectName("input_cantidad")
        self.input_cantidad.setEnabled(False)
        self.input_cantidad.returnPressed.connect(self.agregar_al_carrito)
        self.input_cantidad.installEventFilter(self)
        self.input_cantidad.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                font-size: 15px;
                background-color: #FFFFFF;
                padding: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #2563EB;
            }
        """)
        
        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.setObjectName("btn_primario")
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar.clicked.connect(self.agregar_al_carrito)
        
        caja_cant.addWidget(self.lbl_cant)
        caja_cant.addWidget(self.input_cantidad)
        caja_cant.addWidget(self.btn_agregar)
        
        lbl_v_por = QLabel("Por:")
        lbl_v_por.setStyleSheet("color: #64748B; font-weight: 600; font-size: 13px;")
        
        layout_buscador.addWidget(self.input_buscador, stretch=1)
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
                border-radius: 8px;
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
                background-color: #EBF5FF;
                color: #172033;
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
        
        # Separador visual entre buscador y tabla
        sep_tb = QFrame()
        sep_tb.setFrameShape(QFrame.Shape.HLine)
        sep_tb.setStyleSheet("background-color: #E4E7EC; max-height: 1px; margin-top: 4px; margin-bottom: 4px;")
        layout_tabla.addWidget(sep_tb)
        
        # --- TABLA (CARRITO) Y ESTADO VACÍO ---
        cabecera_tabla = QHBoxLayout()
        lbl_tit_tabla = QLabel("Detalle de la operación")
        lbl_tit_tabla.setStyleSheet("font-size: 14px; font-weight: bold; color: #172033;")
        self.lbl_resumen_rapido = QLabel("0 productos · 0 unidades")
        self.lbl_resumen_rapido.setStyleSheet("color: #64748B; font-weight: 600; font-size: 13px;")
        cabecera_tabla.addWidget(lbl_tit_tabla)
        cabecera_tabla.addStretch()
        cabecera_tabla.addWidget(self.lbl_resumen_rapido)
        
        layout_tabla.addLayout(cabecera_tabla)
        
        self.stack_tabla = QStackedWidget()
        
        # Estado Vacío
        self.lbl_estado_vacio = QLabel("Busque y agregue un producto para comenzar.")
        self.lbl_estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado_vacio.setStyleSheet("color: #94A3B8; font-size: 14px; font-style: italic; background-color: #F8FAFC; border-radius: 8px;")
        self.stack_tabla.addWidget(self.lbl_estado_vacio)
        
        # Tabla Principal
        self.tabla = QTableWidget(0, 9)
        self.tabla.setHorizontalHeaderLabels(["Código", "Descripción", "Unidad", "Cantidad", "Equival.", "Precio Unit.", "Desc. (%)", "Subtotal", ""])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.setShowGrid(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed | QAbstractItemView.EditTrigger.AnyKeyPressed)
        
        self.auto_select_delegate = _AutoSelectDelegate(self.tabla)
        self.tabla.setItemDelegateForColumn(3, self.auto_select_delegate)
        self.tabla.setItemDelegateForColumn(6, self.auto_select_delegate)
        
        # Ajustes de ancho priorizando la descripcion
        self.tabla.setColumnWidth(0, 80)
        self.tabla.setColumnWidth(2, 70)
        self.tabla.setColumnWidth(3, 75)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 110)
        self.tabla.setColumnWidth(6, 75)
        self.tabla.setColumnWidth(7, 120)
        self.tabla.setColumnWidth(8, 40)
        
        self.tabla.itemChanged.connect(self.celda_editada)
        self.stack_tabla.addWidget(self.tabla)
        
        # Inicialmente mostrar el estado vacío
        self.stack_tabla.setCurrentIndex(0)
        
        layout_tabla.addWidget(self.stack_tabla, stretch=1)

        self.contenedor_tabla.setMinimumHeight(220)

        # --- FOOTER: OPCIONES Y RESUMEN COMPACTO ---
        self.contenedor_footer = QFrame()
        self.contenedor_footer.setObjectName("tarjeta_blanca")
        self.contenedor_footer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout_footer = QHBoxLayout(self.contenedor_footer)
        layout_footer.setContentsMargins(16, 12, 16, 12)
        layout_footer.setSpacing(24)
        
        # --- ÁREA IZQUIERDA: OBSERVACIONES ---
        col_izq_footer = QVBoxLayout()
        col_izq_footer.setSpacing(8)
        col_izq_footer.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.chk_descontar = QCheckBox("Descontar del stock físico")
        self.chk_descontar.setChecked(not self.is_presupuesto)
        self.chk_descontar.setEnabled(not self.is_presupuesto)
        if self.is_presupuesto:
            self.chk_descontar.setVisible(False)
        self.chk_descontar.setStyleSheet("color: #475569; font-size: 13px; font-weight: 500;")
        
        fila_obs = QHBoxLayout()
        fila_obs.setSpacing(8)
        lbl_obs = QLabel("Observaciones:")
        lbl_obs.setStyleSheet("color: #475569; font-size: 13px; font-weight: 600;")
        self.input_observaciones = QLineEdit()
        self.input_observaciones.setPlaceholderText("Ej: Entregar por la tarde...")
        self.input_observaciones.setMinimumHeight(36)
        self.input_observaciones.setStyleSheet("border: 1px solid #E4E7EC; border-radius: 6px; font-size: 13px; padding-left: 8px; background-color: #F8FAFC;")
        
        fila_obs.addWidget(lbl_obs)
        fila_obs.addWidget(self.input_observaciones)
        
        col_izq_footer.addWidget(self.chk_descontar)
        col_izq_footer.addLayout(fila_obs)
        
        # Divisor vertical
        div_footer = QFrame()
        div_footer.setFrameShape(QFrame.Shape.VLine)
        div_footer.setStyleSheet("color: #E4E7EC;")
        
        # --- ÁREA DERECHA: TOTALES HORIZONTALES ---
        col_der_footer = QHBoxLayout()
        col_der_footer.setSpacing(20)
        col_der_footer.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        
        # 1. Subtotal
        ly_sub = QVBoxLayout()
        ly_sub.setSpacing(2)
        ly_sub.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_sub_txt = QLabel("Subtotal")
        lbl_sub_txt.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        self.lbl_subtotal = QLabel("$ 0,00")
        self.lbl_subtotal.setStyleSheet("font-size: 15px; font-weight: 600; color: #172033;")
        ly_sub.addWidget(lbl_sub_txt)
        ly_sub.addWidget(self.lbl_subtotal)
        
        # 2. Descuento
        ly_desc = QVBoxLayout()
        ly_desc.setSpacing(2)
        ly_desc.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        ly_desc_top = QHBoxLayout()
        ly_desc_top.setSpacing(4)
        lbl_desc = QLabel("Desc. gral:")
        lbl_desc.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        
        self.input_desc_gral = QLineEdit("0")
        self.input_desc_gral.setFixedWidth(40)
        self.input_desc_gral.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_desc_gral.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 4px; padding: 2px; font-size: 12px; background-color: #FFFFFF; color: #2563EB; font-weight: bold;")
        self.input_desc_gral.editingFinished.connect(self.on_descuento_general_editado)
        self.input_desc_gral.installEventFilter(self)
        
        lbl_desc_pct = QLabel("%")
        lbl_desc_pct.setStyleSheet("color: #64748B; font-size: 12px;")
        
        ly_desc_top.addWidget(lbl_desc)
        ly_desc_top.addWidget(self.input_desc_gral)
        ly_desc_top.addWidget(lbl_desc_pct)
        
        self.lbl_monto_desc = QLabel("-$ 0,00")
        self.lbl_monto_desc.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: 500;")
        ly_desc.addLayout(ly_desc_top)
        ly_desc.addWidget(self.lbl_monto_desc)
        
        # 3. IVA
        ly_iva = QVBoxLayout()
        ly_iva.setSpacing(2)
        ly_iva.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        ly_iva_top = QHBoxLayout()
        ly_iva_top.setSpacing(4)
        
        self.chk_iva = QCheckBox("IVA:")
        self.chk_iva.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        self.chk_iva.stateChanged.connect(self.on_iva_toggled)
        
        self.input_iva_porc = QLineEdit("21")
        self.input_iva_porc.setFixedWidth(40)
        self.input_iva_porc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_iva_porc.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 4px; padding: 2px; font-size: 12px; background-color: #FFFFFF;")
        self.input_iva_porc.setEnabled(False)
        self.input_iva_porc.editingFinished.connect(self.on_iva_editado)
        self.input_iva_porc.installEventFilter(self)
        
        lbl_iva_pct = QLabel("%")
        lbl_iva_pct.setStyleSheet("color: #64748B; font-size: 12px;")
        
        ly_iva_top.addWidget(self.chk_iva)
        ly_iva_top.addWidget(self.input_iva_porc)
        ly_iva_top.addWidget(lbl_iva_pct)
        
        self.lbl_monto_iva = QLabel("+$ 0,00")
        self.lbl_monto_iva.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 500;")
        ly_iva.addLayout(ly_iva_top)
        ly_iva.addWidget(self.lbl_monto_iva)
        
        # 4. Total
        ly_tot = QVBoxLayout()
        ly_tot.setSpacing(0)
        ly_tot.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_tot_t = QLabel("TOTAL")
        lbl_tot_t.setStyleSheet("font-weight: 900; font-size: 12px; color: #172033;")
        self.lbl_total = QLabel("$ 0,00")
        self.lbl_total.setStyleSheet("font-weight: 900; font-size: 24px; color: #2563EB; letter-spacing: -0.5px;")
        ly_tot.addWidget(lbl_tot_t)
        ly_tot.addWidget(self.lbl_total)
        
        # Botón Acción Principal
        if self.is_edicion:
            texto_btn = "Guardar Cambios [F12]"
        else:
            texto_btn = "Crear Presupuesto [F12]" if self.is_presupuesto else "Confirmar Venta [F12]"
            
        self.btn_confirmar = QPushButton(texto_btn)
        self.btn_confirmar.setObjectName("btn_primario")
        self.btn_confirmar.setProperty("tipo", "venta")
        self.btn_confirmar.setFixedHeight(44)
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.clicked.connect(lambda: self.confirmar_operacion(self.tipo_documento_seleccionado))
        
        def div():
            d = QFrame()
            d.setFrameShape(QFrame.Shape.VLine)
            d.setStyleSheet("color: #E4E7EC;")
            return d
            
        col_der_footer.addLayout(ly_sub)
        col_der_footer.addWidget(div())
        col_der_footer.addLayout(ly_desc)
        col_der_footer.addWidget(div())
        col_der_footer.addLayout(ly_iva)
        col_der_footer.addWidget(div())
        col_der_footer.addLayout(ly_tot)
        col_der_footer.addWidget(self.btn_confirmar)
        
        layout_footer.addLayout(col_izq_footer, stretch=1)
        layout_footer.addWidget(div_footer)
        layout_footer.addLayout(col_der_footer, stretch=0)
        
        layout_principal.addWidget(self.contenedor_tabla, stretch=1)
        layout_principal.addWidget(self.contenedor_footer, stretch=0)

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
        
    def deseleccionar_cliente(self):
        self.cliente_seleccionado = None
        self.input_cliente.clear()
        self.widget_tarjeta_cliente.setVisible(False)
        self.widget_busqueda_cliente.setVisible(True)
        self.input_cliente.setFocus()



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
        from db.queries import obtener_productos_frecuentes
        frecuentes = obtener_productos_frecuentes(self.conn, limite=8, dias=30)
        codigos_frec = [f['codigo'] for f in frecuentes]
        
        sugerencias = []
        for cod in codigos_frec:
            for p in self.catalogo:
                if p['codigo'] == cod:
                    sugerencias.append(p)
                    break
                    
        # Fallback si no hay suficientes ventas
        if len(sugerencias) < 4:
            sugerencias = []
            for p in self.catalogo:
                if p['stock'] > 0:
                    sugerencias.append(p)
                if len(sugerencias) >= 8:
                    break
            
            # Si aun no hay 8 con stock, completar con lo que haya
            if len(sugerencias) < 8:
                for p in self.catalogo:
                    if p not in sugerencias:
                        sugerencias.append(p)
                    if len(sugerencias) >= 8:
                        break
                        
        return sugerencias

    def on_buscador_text_changed(self, texto):
        if not self._suspender_resultados and getattr(self, "producto_en_foco", None) is not None:
            self.producto_en_foco = None
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
                    self.on_buscador_text_changed(self.input_buscador.text())
                    return True
                    
        elif obj == self.input_buscador and event.type() == QEvent.Type.FocusIn:
            # Mostrar sugerencias automáticamente si está vacío o tiene texto y no hay producto seleccionado
            if getattr(self, "producto_en_foco", None) is None:
                QTimer.singleShot(0, lambda: self.on_buscador_text_changed(self.input_buscador.text()))
                    
        elif obj == self.combo_unidad and event.type() == QEvent.Type.KeyPress:
            if event.key() in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
                self.input_cantidad.setFocus()
                return True
                
        if obj == self.input_buscador and event.type() == QEvent.Type.FocusOut:
            QTimer.singleShot(100, self.chequear_foco_panel)
            
        if event.type() == QEvent.Type.FocusIn and obj in (self.input_desc_gral, self.input_iva_porc, self.input_cantidad):
            QTimer.singleShot(0, obj.selectAll)
            
        return super().eventFilter(obj, event)

    def chequear_foco_panel(self):
        if not self.input_buscador.hasFocus() and not self.panel_resultados.hasFocus() and not self.lista_resultados.hasFocus():
            self.panel_resultados.hide()

    def on_resultado_clickeado(self, item):
        producto = item.data(Qt.ItemDataRole.UserRole)
        if producto:
            self.seleccionar_producto(producto)

    def seleccionar_producto(self, producto: dict):
        self.producto_en_foco = producto.copy()
        self.panel_resultados.hide()
        
        self._suspender_resultados = True
        self.input_buscador.setText(f"{producto['codigo']} - {producto['desc']}")
        self._suspender_resultados = False
        
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
        return self.chk_descontar.isChecked()

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
        self.input_cantidad.clear()
        self.input_cantidad.setEnabled(False)
        self.combo_unidad.setVisible(False)
        self.lbl_vender_por.setVisible(False)
        self.input_buscador.clear()
        self.input_buscador.setFocus()
        self.actualizar_etiqueta_cantidad()

    def insertar_fila(self, prod, unidad_venta, factor_conversion, cantidad, cantidad_base, precio_unit_mostrado):
        self.tabla.itemChanged.disconnect(self.celda_editada)
        
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
        btn_borrar.clicked.connect(lambda _, r=row: self.borrar_fila_por_boton(r))
        
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
        self.tabla.setCellWidget(row, 8, btn_borrar)
        
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
        self.tabla.itemChanged.connect(self.celda_editada)

    def celda_editada(self, item):
        col = item.column()
        row = item.row()
        
        if col not in [3, 6]: 
            return
            
        prod = self.carrito[row]
        valor = parsear_arg(item.text())

        self.tabla.itemChanged.disconnect(self.celda_editada)
        
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
        
        self.tabla.itemChanged.connect(self.celda_editada)
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

    def borrar_fila_seleccionada(self):
        filas = set([item.row() for item in self.tabla.selectedItems()])
        if not filas: 
            return
        for fila in sorted(filas, reverse=True):
            self.tabla.removeRow(fila)
            del self.carrito[fila]
        self.actualizar_totales()

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
        total_final = subtotal_neto + monto_iva
            
        self.lbl_subtotal.setText(f"$ {formato_arg(subtotal_bruto)}")
        self.lbl_monto_desc.setText(f"-$ {formato_arg(monto_desc_gral)}")
        self.lbl_monto_iva.setText(f"+$ {formato_arg(monto_iva)}")
        self.lbl_total.setText(f"$ {formato_arg(total_final)}")
        
        estado = "🟢 Nueva operación" if not self.carrito else "🟢 En curso"
        
        # Actualizar labels dependientes
        self.lbl_info_items.setText(f"{estado}")
        self.lbl_resumen_rapido.setText(f"{len(self.carrito)} productos · {unidades_totales:g} unidades")
        
        # Actualizar estado vacío
        if not self.carrito:
            self.stack_tabla.setCurrentIndex(0)
        else:
            self.stack_tabla.setCurrentIndex(1)

    def confirmar_operacion(self, tipo):
        if not self.carrito: 
            QMessageBox.information(self, "Venta Vacía", "Agrega al menos un producto para confirmar.")
            return
            
        descontar_stock = self.chk_descontar.isChecked()
        if tipo == 'PRESUPUESTO':
            descontar_stock = False
            estado_doc = 'ACTIVO'
        else:
            estado_doc = 'CONFIRMADO'
            
        fecha_actual = datetime.now()
        
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
            
            self.cargar_catalogo_memoria()
            
            self.operacion_completada.emit(numero_interno)
            
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Error Transaccional", f"Hubo un error al procesar la operación:\n{e}")
