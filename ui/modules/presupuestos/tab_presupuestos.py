"""
ui/modules/presupuestos/tab_presupuestos.py — Pestaña Principal de Presupuestos
"""
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSplitter, QScrollArea, QComboBox, QMessageBox,
    QGridLayout, QDialog, QTextBrowser, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QCursor

from ui.core.theme import (
    COLOR_PRIMARY, COLOR_BG, COLOR_CARD_BG, COLOR_TEXT_MAIN,
    COLOR_TEXT_SEC, COLOR_BORDER, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from ui.core.modal import DialogoModalIntegrado
from ui.components.operacion_base import OperacionBaseWidget
from db import queries_presupuestos as qp
from utils.pdf_documento import generar_pdf_documento

def _fmt_moneda(valor: float) -> str:
    if valor is None: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")



class DialogoDetallePresupuesto(DialogoModalIntegrado):
    def __init__(self, conn, id_documento, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.id_documento = id_documento
        
        det = qp.obtener_detalle_presupuesto(self.conn, self.id_documento)
        if not det:
            self.setWindowTitle("Error")
            ly = QVBoxLayout(self)
            ly.addWidget(QLabel("Error al cargar el presupuesto."))
            return
            
        self.setWindowTitle(f"Detalle de Presupuesto - {det['numero_interno']}")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(650)
        self.resize(1000, 650)
        
        ly = QVBoxLayout(self)
        ly.setContentsMargins(24, 24, 24, 24)
        ly.setSpacing(16)
        
        # Info Header (Cliente y Documento integrados)
        f_info = QFrame()
        f_info.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        ly_info = QHBoxLayout(f_info)
        ly_info.setContentsMargins(24, 24, 24, 24)
        ly_info.setSpacing(40)
        
        # Lado Izquierdo: Cliente
        ly_cli = QVBoxLayout()
        ly_cli.setSpacing(8)
        lbl_cli_t = QLabel("CLIENTE")
        lbl_cli_t.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748b; letter-spacing: 1px;")
        lbl_cli_name = QLabel(det['cliente']['nombre_completo'])
        lbl_cli_name.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        
        lbl_cli_det = QLabel(f"<b>CUIT/DNI:</b> {det['cliente']['cuit_dni'] or '—'}  |  <b>Tel:</b> {det['cliente']['telefono'] or '—'}<br><b>IVA:</b> {det['cliente']['condicion_iva'] or '—'}")
        lbl_cli_det.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SEC};")
        
        ly_cli.addWidget(lbl_cli_t)
        ly_cli.addWidget(lbl_cli_name)
        ly_cli.addWidget(lbl_cli_det)
        ly_cli.addStretch()
        
        # Lado Derecho: Documento
        ly_doc = QVBoxLayout()
        ly_doc.setSpacing(8)
        
        ly_doc_top = QHBoxLayout()
        lbl_doc_t = QLabel(f"PRESUPUESTO {det['numero_interno']}")
        lbl_doc_t.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {COLOR_PRIMARY};")
        
        est = det['estado']
        lbl_estado = QLabel(est)
        lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_estado.setFixedHeight(24)
        if est == 'ACTIVO':
            lbl_estado.setProperty("class", "badge-success")
        elif est == 'VENCIDO':
            lbl_estado.setProperty("class", "badge-danger")
        elif est == 'CONFIRMADO':
            lbl_estado.setProperty("class", "badge-info")
        else:
            lbl_estado.setProperty("class", "badge-neutral")
        lbl_estado.style().unpolish(lbl_estado)
        lbl_estado.style().polish(lbl_estado)
            
        ly_doc_top.addWidget(lbl_doc_t)
        ly_doc_top.addWidget(lbl_estado)
        ly_doc_top.addStretch()
        
        lbl_fechas = QLabel(f"<b>Emisión:</b> {det['fecha_emision']}  |  <b>Vence:</b> {det['fecha_vencimiento'] or '—'}")
        lbl_fechas.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SEC};")
        
        ly_tiempo = QHBoxLayout()
        lbl_tiempo_t = QLabel("<b>Tiempo Restante:</b>")
        lbl_tiempo_t.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SEC};")
        self.lbl_venc_timer = QLabel("—")
        self.lbl_venc_timer.setStyleSheet("font-size: 13px;")
        ly_tiempo.addWidget(lbl_tiempo_t)
        ly_tiempo.addWidget(self.lbl_venc_timer)
        ly_tiempo.addStretch()
        
        ly_doc.addLayout(ly_doc_top)
        ly_doc.addWidget(lbl_fechas)
        ly_doc.addLayout(ly_tiempo)
        ly_doc.addStretch()
        
        ly_info.addLayout(ly_cli, stretch=1)
        
        # Divisor
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet(f"background-color: {COLOR_BORDER};")
        ly_info.addWidget(line)
        
        ly_info.addLayout(ly_doc, stretch=1)
        ly.addWidget(f_info)
        
        # Tabla de Productos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Cantidad", "Unidad", "Precio Unitario", "Subtotal"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; background-color: {COLOR_CARD_BG}; border-radius: 4px;")
        
        detalles = det.get('detalles', [])
        self.tabla.setRowCount(len(detalles))
        for i, item in enumerate(detalles):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(item['descripcion'])))
            
            it_cant = QTableWidgetItem(f"{item['cantidad_unidad_venta']:g}")
            it_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.tabla.setItem(i, 1, it_cant)
            
            it_uni = QTableWidgetItem(str(item['unidad_venta']))
            it_uni.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.tabla.setItem(i, 2, it_uni)
            
            it_precio = QTableWidgetItem(f"$ {_fmt_moneda(item['precio_unitario'])}")
            it_precio.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla.setItem(i, 3, it_precio)
            
            it_sub = QTableWidgetItem(f"$ {_fmt_moneda(item['subtotal'])}")
            it_sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla.setItem(i, 4, it_sub)
            
        ly.addWidget(self.tabla, stretch=1)
        
        # Totales
        ly_totales = QHBoxLayout()
        ly_totales.addStretch()
        
        f_totales = QFrame()
        f_totales.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        ly_t = QHBoxLayout(f_totales)
        ly_t.setContentsMargins(16, 12, 16, 12)
        ly_t.setSpacing(24)
        
        lbl_sub = QLabel(f"<span style='color: {COLOR_TEXT_SEC}; font-size: 13px;'>Subtotal:</span><br><b>$ {_fmt_moneda(det['subtotal_bruto'])}</b>")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_desc = QLabel(f"<span style='color: {COLOR_TEXT_SEC}; font-size: 13px;'>Descuento:</span><br><b>$ {_fmt_moneda(det['total_descuento'])}</b>")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_tot = QLabel(f"<span style='color: {COLOR_TEXT_SEC}; font-size: 13px;'>Total:</span><br><span style='font-size: 20px; color: {COLOR_PRIMARY}; font-weight: 900;'>$ {_fmt_moneda(det['total_final'])}</span>")
        lbl_tot.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        ly_t.addWidget(lbl_sub)
        ly_t.addWidget(lbl_desc)
        
        lin_t = QFrame()
        lin_t.setFrameShape(QFrame.Shape.VLine)
        lin_t.setStyleSheet(f"background-color: {COLOR_BORDER};")
        ly_t.addWidget(lin_t)
        
        ly_t.addWidget(lbl_tot)
        
        ly_totales.addWidget(f_totales)
        ly.addLayout(ly_totales)
        
        # Lógica de Timer
        self.venc_str = det['fecha_vencimiento']
        if det['estado'] == 'ACTIVO' and self.venc_str:
            self.timer_modal = QTimer(self)
            self.timer_modal.setInterval(1000)
            self.timer_modal.timeout.connect(self._actualizar_contador)
            self.timer_modal.start()
            self._actualizar_contador()
        else:
            if det['estado'] == 'VENCIDO':
                self.lbl_venc_timer.setText("Vencido")
                self.lbl_venc_timer.setStyleSheet("color: #dc2626; font-weight: bold;")
            else:
                self.lbl_venc_timer.setText("—")
                
        # Botones Inferiores
        ly_btn = QHBoxLayout()
        ly_btn.addStretch()
        
        btn_preview = QPushButton("Vista Previa")
        btn_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_preview.setMinimumHeight(36)
        btn_preview.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; padding: 0 20px; border-radius: 6px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        btn_preview.clicked.connect(self._abrir_vista_previa)
        
        btn_pdf = QPushButton("Generar PDF")
        btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pdf.setMinimumHeight(36)
        btn_pdf.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; padding: 0 20px; border-radius: 6px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        btn_pdf.clicked.connect(self._generar_pdf)
        
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setMinimumHeight(36)
        btn_cerrar.setStyleSheet(f"background-color: {COLOR_PRIMARY}; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; color: white;")
        btn_cerrar.clicked.connect(self.accept)
        
        ly_btn.addWidget(btn_preview)
        ly_btn.addWidget(btn_pdf)
        ly_btn.addWidget(btn_cerrar)
        ly.addLayout(ly_btn)
        
    def _abrir_vista_previa(self):
        import tempfile, os
        det = qp.obtener_detalle_presupuesto(self.conn, self.id_documento)
        if not det: return
        tmp_path = os.path.join(tempfile.gettempdir(), f"preview_presupuesto_{self.id_documento}.pdf")
        if generar_pdf_documento(det, tmp_path, "PRESUPUESTO"):
            from ui.components.pdf_viewer import DialogoVistaPreviaPDF
            dlg = DialogoVistaPreviaPDF(tmp_path, self.window())
            from PyQt6.QtWidgets import QDialog
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self._generar_pdf()
            
    def _generar_pdf(self):
        det = qp.obtener_detalle_presupuesto(self.conn, self.id_documento)
        if not det: return
        
        import re
        cli_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', det['cliente']['nombre_completo']).strip()
        cli_name = cli_name.replace(' ', '_')
        default_name = f"Presupuesto_{det['numero_interno']}_{cli_name}.pdf"
        
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Presupuesto PDF",
            default_name,
            "Documentos PDF (*.pdf)"
        )
        if file_path:
            try:
                if generar_pdf_documento(det, file_path, "PRESUPUESTO"):
                    from ui.core.modal import DialogoModalIntegrado
                    msg = DialogoModalIntegrado(self.parent())
                    msg.setWindowTitle("Éxito")
                    msg_ly = QVBoxLayout(msg)
                    msg_lbl = QLabel(f"PDF generado correctamente en:<br><br><b>{file_path}</b>")
                    msg_lbl.setWordWrap(True)
                    msg_ly.addWidget(msg_lbl)
                    btn_ok = QPushButton("Aceptar")
                    btn_ok.clicked.connect(msg.accept)
                    msg_ly.addWidget(btn_ok)
                    msg.exec()
                else:
                    QMessageBox.critical(self, "Error", "Error al generar el PDF.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al generar el PDF:\n{e}")

    def _actualizar_contador(self):
        import datetime
        ahora = datetime.datetime.now()
        venc_str = self.venc_str
        try:
            venc_str_clean = venc_str.split(".")[0]
            venc_dt = datetime.datetime.strptime(venc_str_clean, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            venc_dt = datetime.datetime.strptime(venc_str.split(" ")[0], "%Y-%m-%d")
            
        if venc_dt <= ahora:
            self.lbl_venc_timer.setText("Vencido")
            self.lbl_venc_timer.setStyleSheet("color: #dc2626; font-weight: bold;")
            if hasattr(self, 'timer_modal') and self.timer_modal.isActive():
                self.timer_modal.stop()
        else:
            diff = venc_dt - ahora
            segundos = int(diff.total_seconds())
            dias, res = divmod(segundos, 86400)
            horas, res = divmod(res, 3600)
            mins, secs = divmod(res, 60)
            
            if dias > 0:
                texto = f"{dias}d {horas:02d}:{mins:02d}:{secs:02d}"
            else:
                texto = f"{horas:02d}:{mins:02d}:{secs:02d}"
                
            color_text = "#16a34a"
            if dias == 0 and horas < 2:
                color_text = "#dc2626"
            elif dias == 0 and horas < 6:
                color_text = "#ea580c"
                
            self.lbl_venc_timer.setText(texto)
            self.lbl_venc_timer.setStyleSheet(f"color: {color_text}; font-weight: bold;")

    def closeEvent(self, event):
        if hasattr(self, 'timer_modal') and self.timer_modal.isActive():
            self.timer_modal.stop()
        super().closeEvent(event)

class PestanaNuevoPresupuesto(OperacionBaseWidget):
    def __init__(self, conexion_db, is_edicion=False, id_presupuesto_edicion=None):
        super().__init__(conexion_db, is_presupuesto=True, is_edicion=is_edicion, id_presupuesto_edicion=id_presupuesto_edicion)
        self.tipo_documento_seleccionado = 'PRESUPUESTO'
        self.btn_confirmar.setText('Guardar [F12]' if is_edicion else 'Crear Presupuesto [F12]')

    def init_ui(self):
        super().init_ui()
        from PyQt6.QtWidgets import QScrollArea, QFrame, QHBoxLayout
        
        # Envolver el contenido en un QScrollArea para pantallas pequeñas
        main_layout = self.layout()
        if main_layout and main_layout.count() > 0:
            scroll_content = main_layout.itemAt(0).widget()
            if scroll_content:
                # Ocultar encabezado redundante (ya estamos en un Modal)
                layout_principal = scroll_content.layout()
                if layout_principal and layout_principal.count() > 0:
                    ly_tit_item = layout_principal.itemAt(0)
                    if ly_tit_item and isinstance(ly_tit_item, QHBoxLayout):
                        for i in range(ly_tit_item.count()):
                            w = ly_tit_item.itemAt(i).widget()
                            if w: w.hide()
                            
                main_layout.removeWidget(scroll_content)
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                scroll_area.setFrameShape(QFrame.Shape.NoFrame)
                scroll_area.setWidget(scroll_content)
                scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
                main_layout.addWidget(scroll_area)

        # Reducir tamaños fijos "excesivos"
        self.input_buscador.setMinimumHeight(38)
        self.btn_agregar.setFixedHeight(38)
        self.caja_cant_frame.setFixedHeight(38)
        if hasattr(self, 'combo_unidad'):
            self.combo_unidad.setMinimumHeight(38)

    def armar_panel_inferior(self, layout):
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame
        from PyQt6.QtCore import Qt

        ly_main = QVBoxLayout()
        ly_main.setSpacing(6)
        ly_main.setContentsMargins(0, 0, 0, 0)

        # --- FILA 1 ---
        ly_r1 = QHBoxLayout()
        ly_r1.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.input_observaciones.setMinimumWidth(200)
        self.input_observaciones.setMaximumHeight(32)
        self.input_observaciones.setPlaceholderText("Observaciones (opcional)...")
        ly_r1.addWidget(self.input_observaciones)
        
        ly_r1.addStretch()
        
        lbl_desc = QLabel('Desc:')
        lbl_desc.setStyleSheet('color: #64748B; font-weight: 600;')
        ly_r1.addWidget(lbl_desc)
        self.input_desc_gral.setFixedWidth(60)
        self.input_desc_gral.setMaximumHeight(32)
        ly_r1.addWidget(self.input_desc_gral)
        lbl_perc = QLabel('%')
        lbl_perc.setStyleSheet('color: #64748B;')
        ly_r1.addWidget(lbl_perc)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #E2E8F0; margin: 0 8px;")
        ly_r1.addWidget(sep)
        
        self.chk_iva.setStyleSheet("color: #475569; font-weight: 500;")
        ly_r1.addWidget(self.chk_iva)
        self.input_iva_porc.setFixedWidth(60)
        self.input_iva_porc.setMaximumHeight(32)
        ly_r1.addWidget(self.input_iva_porc)
        lbl_perc2 = QLabel('%')
        lbl_perc2.setStyleSheet('color: #64748B;')
        ly_r1.addWidget(lbl_perc2)
        
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #E2E8F0; margin: 0 8px;")
        ly_r1.addWidget(sep2)
        
        lbl_sub = QLabel('Subtotal:')
        lbl_sub.setStyleSheet('color: #64748B; font-weight: 600;')
        ly_r1.addWidget(lbl_sub)
        self.lbl_subtotal.setStyleSheet('color: #64748B; font-size: 13px;')
        self.lbl_subtotal.setMinimumWidth(80)
        self.lbl_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ly_r1.addWidget(self.lbl_subtotal)

        # --- FILA 2 ---
        ly_r2 = QHBoxLayout()
        ly_r2.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        ly_val = QHBoxLayout()
        ly_val.setSpacing(6)
        lbl_validez = QLabel('Validez:')
        lbl_validez.setStyleSheet('color: #64748B; font-weight: 600;')
        ly_val.addWidget(lbl_validez)
        self.combo_validez.setMaximumHeight(32)
        ly_val.addWidget(self.combo_validez)
        ly_r2.addLayout(ly_val)
        
        ly_r2.addStretch()
        
        lbl_tot = QLabel('TOTAL:')
        lbl_tot.setStyleSheet('font-weight: 900; color: #64748B; font-size: 16px;')
        ly_r2.addWidget(lbl_tot)
        
        self.lbl_total.setStyleSheet('font-weight: 900; color: #2563EB; font-size: 24px;')
        self.lbl_total.setMinimumWidth(120)
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ly_r2.addWidget(self.lbl_total)
        
        self.btn_confirmar.setMinimumWidth(160)
        self.btn_confirmar.setMaximumHeight(36)
        ly_r2.addWidget(self.btn_confirmar)
        
        ly_main.addLayout(ly_r1)
        ly_main.addLayout(ly_r2)
        
        layout.addLayout(ly_main)

class DialogoNuevoPresupuesto(DialogoModalIntegrado):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle("Crear Nuevo Presupuesto")
        # Layouts dinámicos y adaptables a resoluciones 1366x768
        self.setMinimumWidth(750)
        self.setMinimumHeight(450)
        self.resize(950, 600)
        
        ly = QVBoxLayout(self)
        ly.setContentsMargins(0, 0, 0, 0)
        
        self.pestana_venta = PestanaNuevoPresupuesto(self.conn)
        self.pestana_venta.setStyleSheet(self.pestana_venta.styleSheet().replace("#F4F7FB", "transparent"))
        self.pestana_venta.operacion_completada.connect(self.accept)
        
        ly.addWidget(self.pestana_venta)
        
class DialogoEditarPresupuesto(DialogoModalIntegrado):
    def __init__(self, conn, id_documento, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle(f"Editar Presupuesto #{id_documento}")
        self.setMinimumWidth(750)
        self.setMinimumHeight(450)
        self.resize(950, 600)
        
        ly = QVBoxLayout(self)
        ly.setContentsMargins(0, 0, 0, 0)
        
        self.pestana_venta = PestanaNuevoPresupuesto(self.conn, is_edicion=True, id_presupuesto_edicion=id_documento)
        self.pestana_venta.setStyleSheet(self.pestana_venta.styleSheet().replace("#F4F7FB", "transparent"))
        self.pestana_venta.operacion_completada.connect(self.accept)
        
        ly.addWidget(self.pestana_venta)


class _TarjetaMetrica(QFrame):
    clicked = pyqtSignal()
    def __init__(self, titulo: str, valor: str = "—", color_borde: str = COLOR_PRIMARY):
        super().__init__()
        self._color_borde = color_borde
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._style(False))
        self.setMinimumWidth(120)
        self.setFixedHeight(75)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(16)

        self._lbl_titulo = QLabel(titulo)
        self._lbl_titulo.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px; font-weight: 600; border: none;")
        self._lbl_valor = QLabel(valor)
        self._lbl_valor.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 18px; font-weight: 900; letter-spacing: -0.5px; border: none;")
        layout.addWidget(self._lbl_titulo)
        layout.addWidget(self._lbl_valor)
        
    def _style(self, selected: bool):
        bg = "#ebf5ff" if selected else COLOR_CARD_BG
        return f"""
            _TarjetaMetrica {{
                background-color: {bg};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                border-left: 4px solid {self._color_borde};
            }}
            _TarjetaMetrica:hover {{ background-color: #f8fafc; }}
        """
        
    def set_valor(self, valor: str):
        self._lbl_valor.setText(valor)
        
    def set_seleccionada(self, sel: bool):
        self.setStyleSheet(self._style(sel))
        
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit()
class DialogoConfirmacionPresupuesto(DialogoModalIntegrado):
    def __init__(self, titulo, mensaje_principal, detalles_html, color_confirmar=COLOR_PRIMARY, txt_confirmar="Confirmar", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(400)
        
        ly = QVBoxLayout(self)
        ly.setSpacing(16)
        
        lbl_msg = QLabel(mensaje_principal)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_MAIN}; font-weight: bold;")
        ly.addWidget(lbl_msg)
        
        frm_det = QFrame()
        frm_det.setStyleSheet(f"background-color: #f8fafc; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        ly_det = QVBoxLayout(frm_det)
        lbl_det = QLabel(detalles_html)
        lbl_det.setWordWrap(True)
        lbl_det.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SEC}; border: none;")
        ly_det.addWidget(lbl_det)
        ly.addWidget(frm_det)
        
        ly_btns = QHBoxLayout()
        ly_btns.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT_MAIN};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #f1f5f9; }}
        """)
        btn_cancelar.clicked.connect(self.reject)
        
        btn_conf = QPushButton(txt_confirmar)
        btn_conf.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_conf.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_confirmar};
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        btn_conf.clicked.connect(self.accept)
        
        ly_btns.addWidget(btn_cancelar)
        ly_btns.addWidget(btn_conf)
        ly.addLayout(ly_btns)

class _CeldaAcciones(QWidget):
    ver_solicitado = pyqtSignal(int)
    editar_solicitado = pyqtSignal(int)
    pdf_solicitado = pyqtSignal(int)
    preview_solicitado = pyqtSignal(int)
    confirmar_solicitado = pyqtSignal(int)
    anular_solicitado = pyqtSignal(int)
    
    def __init__(self, id_documento: int, estado: str):
        super().__init__()
        self._id = id_documento
        self._estado = estado
        
        ly = QHBoxLayout(self)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(0)
        
        btn_more = QPushButton("⋮")
        btn_more.setToolTip("Opciones")
        btn_more.setFixedSize(28, 28)
        btn_more.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_more.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
                color: {COLOR_TEXT_MAIN};
                padding-bottom: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BG};
                border: 1px solid {COLOR_BORDER};
            }}
            QPushButton::menu-indicator {{
                image: none;
                width: 0px;
            }}
        """)
        
        menu = QMenu(btn_more)
        menu.setCursor(Qt.CursorShape.PointingHandCursor)
        menu.setStyleSheet(f"""
            QMenu {{ 
                background-color: {COLOR_CARD_BG}; 
                border: 1px solid {COLOR_BORDER}; 
                border-radius: 6px; 
                padding: 4px; 
            }} 
            QMenu::item {{ 
                padding: 8px 20px; 
                border-radius: 4px; 
                color: {COLOR_TEXT_MAIN}; 
                font-size: 13px; 
            }} 
            QMenu::item:selected {{ 
                background-color: {COLOR_BG}; 
            }} 
            QMenu::separator {{ 
                height: 1px; 
                background-color: {COLOR_BORDER}; 
                margin: 3px 8px; 
            }}
        """)
        
        act_ver = menu.addAction("👁 Ver Detalle")
        act_ver.triggered.connect(lambda: self.ver_solicitado.emit(self._id))
        
        if estado == "ACTIVO":
            act_edit = menu.addAction("✎ Editar")
            act_edit.triggered.connect(lambda: self.editar_solicitado.emit(self._id))
            menu.addSeparator()
            act_conf = menu.addAction("✓ Confirmar como Venta")
            act_conf.triggered.connect(lambda: self.confirmar_solicitado.emit(self._id))
            menu.addSeparator()
            
        act_prev = menu.addAction("📄 Vista Previa")
        act_prev.triggered.connect(lambda: self.preview_solicitado.emit(self._id))
        
        act_pdf = menu.addAction("⬇ Generar PDF")
        act_pdf.triggered.connect(lambda: self.pdf_solicitado.emit(self._id))
        
        if estado in ("ACTIVO", "VENCIDO"):
            menu.addSeparator()
            act_anul = menu.addAction("❌ Anular Presupuesto")
            act_anul.triggered.connect(lambda: self.anular_solicitado.emit(self._id))
            
        btn_more.setMenu(menu)
        ly.addWidget(btn_more, 0, Qt.AlignmentFlag.AlignCenter)

class _PanelVacio(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        ly = QVBoxLayout(self)
        ly.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icono = QLabel("📄")
        icono.setStyleSheet("font-size: 42px; border: none;")
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

        titulo = QLabel("Seleccioná un presupuesto")
        titulo.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {COLOR_TEXT_MAIN}; border: none;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Hacé clic en una fila de la tabla\npara ver el detalle aquí.")
        sub.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SEC}; border: none;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ly.addStretch()
        ly.addWidget(icono)
        ly.addSpacing(8)
        ly.addWidget(titulo)
        ly.addSpacing(4)
        ly.addWidget(sub)
        ly.addStretch()

class _PanelDetalle(QScrollArea):
    ver_detalle_solicitado = pyqtSignal(int)
    editar_solicitado = pyqtSignal(int)
    confirmar_solicitado = pyqtSignal(int)
    anular_solicitado = pyqtSignal(int)
    pdf_solicitado = pyqtSignal(int)
    preview_solicitado = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet(f"QScrollArea {{ border: none; background-color: {COLOR_CARD_BG}; }}")
        self._id_actual = None
        
        self._contenido = QWidget()
        self._contenido.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: none;")
        self._layout = QVBoxLayout(self._contenido)
        self._layout.setContentsMargins(14, 14, 14, 14)
        self._layout.setSpacing(12)
        
        # Titulo y Estado
        self._lbl_num = QLabel("—")
        self._lbl_num.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {COLOR_TEXT_MAIN};")
        
        self._lbl_estado_badge = QLabel("")
        
        ly_num = QHBoxLayout()
        ly_num.addWidget(self._lbl_num)
        ly_num.addWidget(self._lbl_estado_badge)
        ly_num.addStretch()
        
        # Cliente
        self._lbl_cliente = QLabel("—")
        self._lbl_cliente.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        self._lbl_cliente.setWordWrap(True)
        
        self._layout.addLayout(ly_num)
        self._layout.addWidget(self._lbl_cliente)
        
        linea1 = QFrame()
        linea1.setFrameShape(QFrame.Shape.HLine)
        linea1.setStyleSheet(f"background-color: {COLOR_BORDER}; margin: 4px 0px;")
        self._layout.addWidget(linea1)
        
        # Validez y Reloj (Centrado)
        self._lbl_validez = QLabel("—")
        self._lbl_validez.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {COLOR_PRIMARY};")
        self._lbl_validez.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_validez.setWordWrap(True)
        
        self._lbl_validez_desc = QLabel("restantes")
        self._lbl_validez_desc.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SEC}; font-weight: bold; text-transform: uppercase;")
        self._lbl_validez_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ly_der = QVBoxLayout()
        ly_der.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ly_der.setSpacing(2)
        ly_der.addWidget(self._lbl_validez)
        ly_der.addWidget(self._lbl_validez_desc)
        
        self._layout.addLayout(ly_der)
        
        linea2 = QFrame()
        linea2.setFrameShape(QFrame.Shape.HLine)
        linea2.setStyleSheet(f"background-color: {COLOR_BORDER}; margin: 4px 0px;")
        self._layout.addWidget(linea2)
        
        # Info secundaria
        self._lbl_fechas = QLabel("—")
        self._lbl_fechas.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SEC};")
        self._lbl_fechas.setWordWrap(True)
        self._layout.addWidget(self._lbl_fechas)
        
        self._lbl_items = QLabel("—")
        self._lbl_items.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SEC};")
        self._layout.addWidget(self._lbl_items)
        
        self._layout.addSpacing(4)
        
        # Total
        self._lbl_total = QLabel("—")
        self._lbl_total.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {COLOR_TEXT_MAIN};")
        self._layout.addWidget(self._lbl_total)
        
        # Observaciones
        self._lbl_obs = QLabel("")
        self._lbl_obs.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SEC}; font-style: italic;")
        self._lbl_obs.setWordWrap(True)
        self._layout.addWidget(self._lbl_obs)
        
        self._layout.addStretch()
        
        # Botones
        ly_btns = QGridLayout()
        ly_btns.setSpacing(8)
        
        self._btn_ver = QPushButton("Ver detalle")
        self._btn_ver.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_ver.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; padding: 8px; border-radius: 6px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        self._btn_ver.clicked.connect(lambda: self.ver_detalle_solicitado.emit(self._id_actual) if self._id_actual else None)
        
        self._btn_editar = QPushButton("Editar")
        self._btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_editar.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; padding: 8px; border-radius: 6px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        self._btn_editar.clicked.connect(lambda: self.editar_solicitado.emit(self._id_actual) if self._id_actual else None)
        
        self._btn_preview = QPushButton("Vista Previa")
        self._btn_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_preview.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; padding: 8px; border-radius: 6px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        self._btn_preview.clicked.connect(lambda: self.preview_solicitado.emit(self._id_actual) if self._id_actual else None)

        self._btn_pdf = QPushButton("PDF")
        self._btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_pdf.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; padding: 8px; border-radius: 6px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        self._btn_pdf.clicked.connect(lambda: self.pdf_solicitado.emit(self._id_actual) if self._id_actual else None)
        
        self._btn_confirmar = QPushButton("Confirmar Venta")
        self._btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_confirmar.setStyleSheet(f"background-color: {COLOR_PRIMARY}; border: 1px solid {COLOR_PRIMARY}; padding: 8px; border-radius: 6px; font-weight: bold; color: white;")
        self._btn_confirmar.clicked.connect(lambda: self.confirmar_solicitado.emit(self._id_actual) if self._id_actual else None)
        
        self._btn_anular = QPushButton("Anular")
        self._btn_anular.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_anular.setStyleSheet(f"background-color: #fee2e2; border: 1px solid #fca5a5; padding: 8px; border-radius: 6px; font-weight: bold; color: {COLOR_DANGER};")
        self._btn_anular.clicked.connect(lambda: self.anular_solicitado.emit(self._id_actual) if self._id_actual else None)
        
        ly_btns.addWidget(self._btn_ver, 0, 0)
        ly_btns.addWidget(self._btn_editar, 0, 1)
        ly_btns.addWidget(self._btn_preview, 1, 0)
        ly_btns.addWidget(self._btn_pdf, 1, 1)
        ly_btns.addWidget(self._btn_confirmar, 2, 0, 1, 2)
        ly_btns.addWidget(self._btn_anular, 3, 0, 1, 2)
        
        self._layout.addLayout(ly_btns)
        
        self.setWidget(self._contenido)
        
    def cargar(self, conn, id_documento: int):
        self._id_actual = id_documento
        det = qp.obtener_detalle_presupuesto(conn, id_documento)
        if not det: return
        
        self._lbl_num.setText(f"{det['numero_interno']}")
        
        est = det['estado']
        if est == 'ACTIVO':
            self._lbl_estado_badge.setProperty("class", "badge-success")
        elif est == 'VENCIDO':
            self._lbl_estado_badge.setProperty("class", "badge-danger")
        elif est == 'CONFIRMADO':
            self._lbl_estado_badge.setProperty("class", "badge-info")
        else:
            self._lbl_estado_badge.setProperty("class", "badge-neutral")
        
        self._lbl_estado_badge.style().unpolish(self._lbl_estado_badge)
        self._lbl_estado_badge.style().polish(self._lbl_estado_badge)
        self._lbl_estado_badge.setText(f"{est}")
        
        self._lbl_cliente.setText(det['cliente']['nombre_completo'])
        self._lbl_fechas.setText(f"Emisión: {det['fecha_emision'][:10]}")
        
        if est == 'ACTIVO':
            self._lbl_validez.setText(f"⏱ Calculando...")
            self._lbl_validez.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {COLOR_PRIMARY};")
            self._lbl_validez_desc.show()
        else:
            self._lbl_validez_desc.hide()
            self._lbl_validez.setText(est)
            if est == 'VENCIDO':
                self._lbl_validez.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_DANGER};")
            elif est == 'CONFIRMADO':
                self._lbl_validez.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_SUCCESS};")
            else:
                self._lbl_validez.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_SEC};")
        self._lbl_items.setText(f"Ítems: {len(det['detalles'])}")
        self._lbl_total.setText(f"Total: {_fmt_moneda(det['total_final'])}")
        
        obs = det['observaciones']
        self._lbl_obs.setText(f"Notas: {obs}" if obs else "Sin observaciones.")
        
        self._btn_editar.setVisible(det['estado'] == 'ACTIVO')
        self._btn_confirmar.setVisible(det['estado'] == 'ACTIVO')
        self._btn_anular.setVisible(det['estado'] in ('ACTIVO', 'VENCIDO'))

class PestanaPresupuestos(QWidget):
    _OPCIONES_POR_PAGINA = [20, 50, 100]

    def __init__(self, conexion_db):
        super().__init__()
        self.conn = conexion_db
        self._filtro_texto: str = ""
        self._estado_actual: str = "TODOS"
        self._pagina_actual: int = 1
        self._por_pagina = 20
        self._total_paginas = 1
        self._id_seleccionado: int | None = None
        self._lista_activos = [] # Para el temporizador
        
        self._timer_busqueda = QTimer(self)
        self._timer_busqueda.setSingleShot(True)
        self._timer_busqueda.setInterval(350)
        self._timer_busqueda.timeout.connect(self._aplicar_filtros)
        
        self._timer_validez = QTimer(self)
        self._timer_validez.setInterval(1000)
        self._timer_validez.timeout.connect(self._on_timer_validez_tick)

        self._init_ui()
        self.recargar()
        self._timer_validez.start()

    def _init_ui(self):
        self.setStyleSheet(self._stylesheet())
        ly = QVBoxLayout(self)
        ly.setContentsMargins(20, 16, 20, 16)
        ly.setSpacing(16)

        ly.addLayout(self._construir_encabezado())
        ly.addLayout(self._construir_metricas())
        ly.addWidget(self._construir_panel_filtros())
        ly.addWidget(self._construir_cuerpo(), stretch=1)
        ly.addLayout(self._construir_paginacion())

    def _stylesheet(self) -> str:
        return f"""
            PestanaPresupuestos {{ background-color: {COLOR_BG}; }}
            QLineEdit, QComboBox {{
                padding: 6px 10px; font-size: 13px;
                border: 1px solid {COLOR_BORDER}; border-radius: 6px;
                background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN};
            }}
            QLineEdit:focus, QComboBox:focus {{ border: 1px solid {COLOR_PRIMARY}; }}
            QPushButton.primario {{
                background-color: {COLOR_PRIMARY}; color: white; font-weight: bold; font-size: 13px;
                padding: 8px 16px; border-radius: 6px; border: none;
            }}
            QPushButton.primario:hover {{ background-color: #1d4ed8; }}
            QPushButton.secundario {{
                background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; font-weight: 600; font-size: 13px;
                padding: 8px 16px; border-radius: 6px; border: 1px solid {COLOR_BORDER};
            }}
            QPushButton.secundario:hover {{ background-color: {COLOR_BG}; }}
            QPushButton.pagina {{
                background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; font-size: 13px;
                padding: 5px 12px; border-radius: 5px; border: 1px solid {COLOR_BORDER}; min-width: 32px;
            }}
            QPushButton.pagina:hover {{ background-color: {COLOR_BG}; border-color: {COLOR_PRIMARY}; }}
            QPushButton.pagina:disabled {{ color: {COLOR_BORDER}; background-color: {COLOR_BG}; }}
            QTableWidget {{
                border: 1px solid {COLOR_BORDER}; border-radius: 6px; gridline-color: {COLOR_BORDER};
                background-color: {COLOR_CARD_BG}; outline: none; font-size: 13px;
            }}
            QHeaderView::section {{
                background-color: {COLOR_BG}; color: {COLOR_TEXT_SEC}; font-weight: 700; font-size: 12px;
                border: none; border-bottom: 1px solid {COLOR_BORDER}; padding: 10px 8px;
            }}
            QTableWidget::item {{ border-bottom: 1px solid #f1f5f9; padding: 4px 8px; color: {COLOR_TEXT_MAIN}; }}
            QTableWidget::item:selected {{ background-color: {COLOR_PRIMARY}; color: white; }}
        """

    def _construir_encabezado(self) -> QHBoxLayout:
        from ui.components.encabezado import crear_encabezado_estandar
        ly_izq, btn_ayuda = crear_encabezado_estandar(
            "📄", "Presupuestos", "Seguimiento, validez y gestión de presupuestos"
        )
        btn_ayuda.clicked.connect(self._mostrar_ayuda)

        ly = QHBoxLayout()
        self._btn_nuevo = QPushButton("+ Nuevo Presupuesto")
        self._btn_nuevo.setProperty("class", "primario")
        self._btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_nuevo.clicked.connect(self._abrir_modal_nuevo_presupuesto)

        ly.addLayout(ly_izq)
        ly.addStretch()
        ly.addWidget(btn_ayuda, alignment=Qt.AlignmentFlag.AlignTop)
        ly.addWidget(self._btn_nuevo, alignment=Qt.AlignmentFlag.AlignTop)
        return ly

    def _mostrar_ayuda(self):
        from ui.components.ayuda import DialogoAyudaContextual
        texto = (
            "<p><b>FUNCIONES PRINCIPALES:</b></p>"
            "<ul>"
            "<li><b>Creación y Consulta:</b> Podés crear nuevos presupuestos y consultar el listado histórico completo.</li>"
            "<li><b>Estados:</b> Cada presupuesto atraviesa distintas etapas: ACTIVO, VENCIDO, CONFIRMADO (venta realizada) o ANULADO.</li>"
            "<li><b>Validez (Cuenta regresiva):</b> Tienen un vencimiento de 48 horas. Una cuenta regresiva visual te indica el tiempo restante en color verde, naranja (próximo a vencer) o rojo.</li>"
            "</ul>"
            "<p><b>COMPROMISO DE STOCK (ATP):</b></p>"
            "<ul>"
            "<li>Un presupuesto <b>ACTIVO</b> compromete temporalmente la disponibilidad de los artículos, para asegurar la reserva sin descontar el stock físico real.</li>"
            "<li>Al vencerse, el sistema <b>libera automáticamente</b> este compromiso temporal.</li>"
            "</ul>"
            "<p><b>ACCIONES POR PRESUPUESTO:</b></p>"
            "<ul>"
            "<li><b>👁 (Ver):</b> Abre el detalle completo, válido en cualquier estado.</li>"
            "<li><b>✎ (Editar):</b> Permite modificar el presupuesto, <b>únicamente si está ACTIVO</b>.</li>"
            "<li><b>⋮ (Menú de acciones):</b> Permite Confirmar como Venta (solo ACTIVO), Anular (solo ACTIVO), generar una Vista Previa o Exportar a PDF.</li>"
            "</ul>"
            "<p><b>ATAJOS DE TECLADO:</b></p>"
            "<ul>"
            "<li><b>Escape:</b> Cerrar cualquier diálogo abierto.</li>"
            "</ul>"
        )
        dialogo = DialogoAyudaContextual("Ayuda: Módulo Presupuestos", "Gestión de presupuestos y compromisos de stock", texto, self)
        dialogo.exec()

    def _construir_metricas(self) -> QHBoxLayout:
        ly = QHBoxLayout()
        ly.setSpacing(12)
        self._mk_total = _TarjetaMetrica("TOTAL PRESUPUESTOS", "0", "#3b82f6")
        self._mk_activos = _TarjetaMetrica("ACTIVOS", "0", COLOR_SUCCESS)
        self._mk_vencidos = _TarjetaMetrica("VENCIDOS", "0", COLOR_DANGER)
        self._mk_anulados = _TarjetaMetrica("CANCELADOS", "0", "#94a3b8")
        
        self._mk_total.clicked.connect(lambda: self._cambiar_estado_kpi("TODOS", self._mk_total))
        self._mk_activos.clicked.connect(lambda: self._cambiar_estado_kpi("ACTIVO", self._mk_activos))
        self._mk_vencidos.clicked.connect(lambda: self._cambiar_estado_kpi("VENCIDO", self._mk_vencidos))
        self._mk_anulados.clicked.connect(lambda: self._cambiar_estado_kpi("ANULADO", self._mk_anulados))

        for mk in [self._mk_total, self._mk_activos, self._mk_vencidos, self._mk_anulados]:
            ly.addWidget(mk)
            
        self._mk_total.set_seleccionada(True)
        self._tarjeta_activa = self._mk_total
        return ly

    def _construir_panel_filtros(self) -> QFrame:
        f = QFrame()
        f.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        ly = QHBoxLayout(f)
        ly.setContentsMargins(12, 10, 12, 10)
        ly.setSpacing(12)

        self._in_busqueda = QLineEdit()
        self._in_busqueda.setPlaceholderText("Buscar por N°, Cliente...")
        self._in_busqueda.setFixedWidth(250)
        self._in_busqueda.textChanged.connect(lambda: self._timer_busqueda.start())

        self._cb_estado = QComboBox()
        self._cb_estado.addItems(["Todos los estados", "Activos", "Vencidos", "Anulados", "Confirmados"])
        self._cb_estado.currentIndexChanged.connect(self._on_combo_estado_changed)
        
        ly.addWidget(self._in_busqueda)
        ly.addWidget(QLabel("Estado:"))
        ly.addWidget(self._cb_estado)
        ly.addStretch()
        return f

    def _construir_cuerpo(self) -> QSplitter:
        spl = QSplitter(Qt.Orientation.Horizontal)
        spl.setHandleWidth(8)
        spl.setStyleSheet(f"QSplitter::handle {{ background-color: transparent; }}")

        self._tabla = QTableWidget(0, 7)
        self._tabla.setHorizontalHeaderLabels(["N°", "Cliente", "Fecha", "Validez", "Total", "Estado", "Acciones"])
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla.setShowGrid(True)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.verticalHeader().setDefaultSectionSize(56)
        
        hdr = self._tabla.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(0, 90)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(2, 130)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(3, 160)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(4, 150)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(5, 140)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._tabla.setColumnWidth(6, 110)
        item_acc = self._tabla.horizontalHeaderItem(6)
        if item_acc:
            item_acc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._tabla.itemSelectionChanged.connect(self._on_seleccion_cambiada)
        
        spl.addWidget(self._tabla)

        self._panel_vacio = _PanelVacio()
        self._panel_detalle = _PanelDetalle()
        self._panel_detalle.ver_detalle_solicitado.connect(self._abrir_modal_detalle)
        self._panel_detalle.editar_solicitado.connect(self._editar_presupuesto)
        self._panel_detalle.confirmar_solicitado.connect(self._confirmar_como_venta)
        self._panel_detalle.anular_solicitado.connect(self._anular_presupuesto)
        self._panel_detalle.pdf_solicitado.connect(self._generar_pdf)
        self._panel_detalle.preview_solicitado.connect(self._abrir_vista_previa)
        
        ly_der = QVBoxLayout()
        ly_der.setContentsMargins(0, 0, 0, 0)
        ly_der.addWidget(self._panel_vacio)
        ly_der.addWidget(self._panel_detalle)
        
        w_der = QWidget()
        w_der.setLayout(ly_der)
        w_der.setMinimumWidth(280)
        spl.addWidget(w_der)

        spl.setStretchFactor(0, 7)
        spl.setStretchFactor(1, 3)
        return spl

    def _construir_paginacion(self) -> QHBoxLayout:
        ly = QHBoxLayout()
        self._lbl_info_pag = QLabel("0 presupuestos")
        self._lbl_info_pag.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px; border: none;")
        ly.addWidget(self._lbl_info_pag)
        ly.addStretch()
        
        ly.addWidget(QLabel("Mostrar:"))
        self._cb_por_pagina = QComboBox()
        self._cb_por_pagina.addItems([str(x) for x in self._OPCIONES_POR_PAGINA])
        self._cb_por_pagina.currentIndexChanged.connect(self._on_por_pagina_changed)
        ly.addWidget(self._cb_por_pagina)
        ly.addSpacing(10)
        
        self._btn_prev = QPushButton("Anterior")
        self._btn_prev.setProperty("class", "pagina")
        self._btn_prev.clicked.connect(self._pagina_anterior)
        self._lbl_pag_actual = QLabel("Pág. 1")
        self._lbl_pag_actual.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: bold; font-size: 12px; margin: 0 10px;")
        self._btn_next = QPushButton("Siguiente")
        self._btn_next.setProperty("class", "pagina")
        self._btn_next.clicked.connect(self._pagina_siguiente)
        
        ly.addWidget(self._btn_prev)
        ly.addWidget(self._lbl_pag_actual)
        ly.addWidget(self._btn_next)
        return ly

    # ──────────────────────────────────────────────────────────────────────────
    # LOGICA DE UI
    # ──────────────────────────────────────────────────────────────────────────
    
    def _cambiar_estado_kpi(self, estado: str, tarjeta: _TarjetaMetrica):
        self._tarjeta_activa.set_seleccionada(False)
        tarjeta.set_seleccionada(True)
        self._tarjeta_activa = tarjeta
        self._estado_actual = estado
        
        mapeo_idx = {"TODOS": 0, "ACTIVO": 1, "VENCIDO": 2, "ANULADO": 3, "CONFIRMADO": 4}
        if estado in mapeo_idx:
            self._cb_estado.blockSignals(True)
            self._cb_estado.setCurrentIndex(mapeo_idx[estado])
            self._cb_estado.blockSignals(False)
            
        self._pagina_actual = 1
        self.recargar()

    def _on_combo_estado_changed(self, idx: int):
        mapeo = {0: "TODOS", 1: "ACTIVO", 2: "VENCIDO", 3: "ANULADO", 4: "CONFIRMADO"}
        estado = mapeo.get(idx, "TODOS")
        self._estado_actual = estado
        
        self._tarjeta_activa.set_seleccionada(False)
        if estado == "TODOS": self._tarjeta_activa = self._mk_total
        elif estado == "ACTIVO": self._tarjeta_activa = self._mk_activos
        elif estado == "VENCIDO": self._tarjeta_activa = self._mk_vencidos
        elif estado == "ANULADO": self._tarjeta_activa = self._mk_anulados
        else: self._tarjeta_activa = self._mk_total
        self._tarjeta_activa.set_seleccionada(True)
        
        self._pagina_actual = 1
        self.recargar()
        
    def _aplicar_filtros(self):
        self._filtro_texto = self._in_busqueda.text().strip()
        self._pagina_actual = 1
        self.recargar()
        
    def _on_por_pagina_changed(self):
        self._por_pagina = int(self._cb_por_pagina.currentText())
        self._pagina_actual = 1
        self.recargar()
        
    def _pagina_anterior(self):
        if self._pagina_actual > 1:
            self._pagina_actual -= 1
            self.recargar()
            
    def _pagina_siguiente(self):
        if self._pagina_actual < self._total_paginas:
            self._pagina_actual += 1
            self.recargar()
            
    def _actualizar_colores_seleccion(self):
        sel_rows = {item.row() for item in self._tabla.selectedItems()}
        for r in range(self._tabla.rowCount()):
            is_sel = r in sel_rows
            
            # Columna Validez (3)
            w_val = self._tabla.cellWidget(r, 3)
            if w_val:
                lbls = w_val.findChildren(QLabel)
                if len(lbls) >= 2:
                    lbl_f = lbls[0]
                    lbl_t = lbls[1]
                    color_f = "white" if is_sel else COLOR_TEXT_SEC
                    lbl_f.setStyleSheet(f"color: {color_f}; font-size: 11px;")
                    
                    # If lbl_t has no background (ANULADO/CONFIRMADO), update it too
                    # We can check its current text or style
                    if "background-color" not in lbl_t.styleSheet():
                        lbl_t.setStyleSheet(f"color: {color_f}; font-weight: bold; font-size: 12px;")
            
            # Columna Acciones (6)
            w_acc = self._tabla.cellWidget(r, 6)
            if w_acc:
                btns = w_acc.findChildren(QPushButton)
                if btns:
                    btn = btns[0]
                    color_btn = "white" if is_sel else COLOR_TEXT_MAIN
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: transparent;
                            border: 1px solid transparent;
                            border-radius: 4px;
                            font-size: 18px;
                            font-weight: bold;
                            color: {color_btn};
                        }}
                        QPushButton:hover {{
                            background-color: {COLOR_BG};
                            border: 1px solid {COLOR_BORDER};
                            color: {COLOR_TEXT_MAIN};
                        }}
                        QPushButton::menu-indicator {{ image: none; width: 0px; }}
                    """)

    def _on_seleccion_cambiada(self):
        self._actualizar_colores_seleccion()
        sel = self._tabla.selectedItems()
        if not sel:
            self._id_seleccionado = None
            self._panel_detalle.hide()
            self._panel_vacio.show()
            return
            
        fila = sel[0].row()
        id_doc = self._tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)
        
        if self._id_seleccionado == id_doc:
            self._tabla.clearSelection()
            return
            
        self._id_seleccionado = id_doc
        self._panel_vacio.hide()
        self._panel_detalle.show()
        self._panel_detalle.cargar(self.conn, id_doc)
        
        # Sincronizar el texto de validez inmediato en el panel
        for item in self._lista_activos:
            if item["id_documento"] == id_doc:
                it_val = self._tabla.item(item["fila"], 3)
                if it_val:
                    self._panel_detalle._lbl_validez.setText(f"Validez: {it_val.text()}")
                break

    def _abrir_modal_detalle(self, id_documento: int):
        dlg = DialogoDetallePresupuesto(self.conn, id_documento, parent=self.window())
        dlg.exec()

    def _abrir_modal_nuevo_presupuesto(self):
        vp = self.window()
        if hasattr(vp, 'crear_operacion'):
            vp.crear_operacion("PRESUPUESTO")
            
    def _editar_presupuesto(self, id_documento: int):
        vp = self.window()
        if hasattr(vp, 'crear_operacion'):
            vp.crear_operacion("PRESUPUESTO", is_edicion=True, id_edicion=id_documento)

    def _abrir_vista_previa(self, id_documento: int):
        import tempfile, os
        det = qp.obtener_detalle_presupuesto(self.conn, id_documento)
        if not det: return
        tmp_path = os.path.join(tempfile.gettempdir(), f"preview_presupuesto_{id_documento}.pdf")
        if generar_pdf_documento(det, tmp_path, "PRESUPUESTO"):
            from ui.components.pdf_viewer import DialogoVistaPreviaPDF
            dlg = DialogoVistaPreviaPDF(tmp_path, self.window())
            from PyQt6.QtWidgets import QDialog
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self._generar_pdf(id_documento)
            
    def _generar_pdf(self, id_documento: int):
        det = qp.obtener_detalle_presupuesto(self.conn, id_documento)
        if not det: return
        
        import re
        cli_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', det['cliente']['nombre_completo']).strip()
        cli_name = cli_name.replace(' ', '_')
        default_name = f"Presupuesto_{det['numero_interno']}_{cli_name}.pdf"
        
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Presupuesto PDF",
            default_name,
            "Documentos PDF (*.pdf)"
        )
        if file_path:
            try:
                if generar_pdf_documento(det, file_path, "PRESUPUESTO"):
                    from ui.core.modal import DialogoModalIntegrado
                    msg = DialogoModalIntegrado(self.window())
                    msg.setWindowTitle("Éxito")
                    msg_ly = QVBoxLayout(msg)
                    msg_lbl = QLabel(f"PDF generado correctamente en:<br><br><b>{file_path}</b>")
                    msg_lbl.setWordWrap(True)
                    msg_ly.addWidget(msg_lbl)
                    btn_ok = QPushButton("Aceptar")
                    btn_ok.clicked.connect(msg.accept)
                    msg_ly.addWidget(btn_ok)
                    msg.exec()
                else:
                    QMessageBox.critical(self, "Error", "Error al generar el PDF.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al generar el PDF:\n{e}")

    def _anular_presupuesto(self, id_documento: int):
        det = qp.obtener_detalle_presupuesto(self.conn, id_documento)
        if not det or det['estado'] not in ('ACTIVO', 'VENCIDO'):
            from ui.core.modal import DialogoModalIntegrado
            msg = DialogoModalIntegrado(self.window())
            msg.setWindowTitle("Error")
            msg_ly = QVBoxLayout(msg)
            lbl = QLabel("El presupuesto no se puede anular porque ya no está ACTIVO ni VENCIDO.")
            lbl.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_MAIN};")
            msg_ly.addWidget(lbl)
            btn = QPushButton("Aceptar")
            btn.clicked.connect(msg.accept)
            msg_ly.addWidget(btn)
            msg.exec()
            return
            
        detalles = f"Cliente: <b>{det['cliente']['nombre_completo']}</b><br><br>Al anularlo, se <b>liberará todo el stock comprometido</b> de forma inmediata. Esta acción no se puede deshacer y no eliminará el registro histórico."
        dlg = DialogoConfirmacionPresupuesto(
            titulo="Confirmar Anulación",
            mensaje_principal=f"¿Estás seguro de anular el presupuesto <b>{det['numero_interno']}</b>?",
            detalles_html=detalles,
            color_confirmar=COLOR_DANGER,
            txt_confirmar="Sí, anular",
            parent=self.window()
        )
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                qp.anular_presupuesto(self.conn, id_documento)
                self._notificar_cambios_globales()
            except Exception as e:
                # Usar QMessageBox genérico para crash de DB inesperado está bien, o uno integrado
                QMessageBox.critical(self, "Error", f"Ocurrió un error al anular:\n{e}")

    def _confirmar_como_venta(self, id_documento: int):
        det = qp.obtener_detalle_presupuesto(self.conn, id_documento)
        if not det or det['estado'] != 'ACTIVO':
            from ui.core.modal import DialogoModalIntegrado
            msg = DialogoModalIntegrado(self.window())
            msg.setWindowTitle("Error")
            msg_ly = QVBoxLayout(msg)
            lbl = QLabel("El presupuesto no se puede confirmar porque ya no está ACTIVO.")
            lbl.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_MAIN};")
            msg_ly.addWidget(lbl)
            btn = QPushButton("Aceptar")
            btn.clicked.connect(msg.accept)
            msg_ly.addWidget(btn)
            msg.exec()
            return
            
        cant_prods = len(det['detalles'])
        total_formateado = f"$ {det['total_final']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        detalles = (
            f"Cliente: <b>{det['cliente']['nombre_completo']}</b><br>"
            f"Total: <b>{total_formateado}</b><br>"
            f"Productos: <b>{cant_prods} ítem(s)</b><br><br>"
            f"⚠️ Esta acción es irreversible. Consumirá el material comprometido y registrará la salida física del inventario de forma inmediata."
        )
        
        dlg = DialogoConfirmacionPresupuesto(
            titulo="Confirmar como Venta",
            mensaje_principal=f"¿Deseas confirmar el presupuesto <b>{det['numero_interno']}</b> como venta real?",
            detalles_html=detalles,
            color_confirmar=COLOR_PRIMARY,
            txt_confirmar="Confirmar Venta",
            parent=self.window()
        )
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                num_venta = qp.confirmar_presupuesto(self.conn, id_documento)
                self._notificar_cambios_globales()
                
                # Lanzar modal de éxito usando DialogoVentaExitosa y pasando el origen extra
                from ui.components.operacion_base import DialogoVentaExitosa
                from datetime import datetime
                cant_unidades = sum(d['cantidad_unidad_venta'] for d in det['detalles'])
                
                cli_origen = f"{det['cliente']['nombre_completo']}\n(Origen: Presupuesto {det['numero_interno']})"
                
                exito_dlg = DialogoVentaExitosa(
                    conn=self.conn,
                    id_documento=id_documento,
                    num_venta=num_venta,
                    cliente_txt=cli_origen,
                    fecha_hora=datetime.now().strftime("%d/%m/%Y %H:%M"),
                    cant_prods=cant_prods,
                    cant_unidades=cant_unidades,
                    total=total_formateado,
                    desconto_stock="Sí",
                    is_presupuesto=False,
                    parent=self.window()
                )
                exito_dlg.setWindowTitle("✓ Venta confirmada correctamente")
                exito_dlg.exec()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un error al confirmar la venta:\n{e}")

    # ──────────────────────────────────────────────────────────────────────────
    # TIMER DE VALIDEZ (CUENTA REGRESIVA)
    # ──────────────────────────────────────────────────────────────────────────

    def _on_timer_validez_tick(self):
        if not self._lista_activos:
            return
            
        ahora = datetime.datetime.now()
        hay_vencidos_nuevos = False
        
        for item in self._lista_activos:
            venc_str = item["vencimiento"]
            if not venc_str: continue
            
            try:
                venc_str_clean = venc_str.split(".")[0]
                venc_dt = datetime.datetime.strptime(venc_str_clean, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    venc_dt = datetime.datetime.strptime(venc_str.split(" ")[0], "%Y-%m-%d")
                except ValueError:
                    continue
                    
            if venc_dt <= ahora:
                texto = "Vencido"
                hay_vencidos_nuevos = True
                color_text = COLOR_DANGER
                bg_color = "#fee2e2"
                fg_color = "#991b1b"
            else:
                diff = venc_dt - ahora
                segundos = int(diff.total_seconds())
                dias, res = divmod(segundos, 86400)
                horas, res = divmod(res, 3600)
                mins, secs = divmod(res, 60)
                if dias > 0:
                    texto = f"⏱ {dias} d {horas:02d}:{mins:02d}:{secs:02d}"
                    color_text = COLOR_SUCCESS
                    bg_color = "#dcfce7"
                    fg_color = "#166534"
                else:
                    texto = f"⏱ {horas:02d}:{mins:02d}:{secs:02d}"
                    if horas < 2:
                        color_text = COLOR_DANGER
                        bg_color = "#fee2e2"
                        fg_color = "#991b1b"
                    elif horas < 6:
                        color_text = COLOR_WARNING
                        bg_color = "#ffedd5"
                        fg_color = "#9a3412"
                    else:
                        color_text = COLOR_SUCCESS
                        bg_color = "#dcfce7"
                        fg_color = "#166534"
                    
            # Actualizar celda sin romper la selección
            lbl_timer = item.get("lbl_timer")
            if lbl_timer and lbl_timer.text() != texto:
                lbl_timer.setText(texto)
                lbl_timer.setStyleSheet(f"color: {fg_color}; font-weight: 800; font-size: 12px; background-color: {bg_color}; border-radius: 4px; padding: 2px 6px;")
                    
            # Sincronizar panel lateral si el item está seleccionado
            if self._id_seleccionado == item["id_documento"]:
                self._panel_detalle._lbl_validez.setText(f"{texto}")
                self._panel_detalle._lbl_validez.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {color_text};")
                if texto == "Vencido":
                    self._panel_detalle._lbl_validez_desc.hide()
                else:
                    self._panel_detalle._lbl_validez_desc.show()
                    
        # Trigger exact moment SQL sync if something crossed 0
        if hay_vencidos_nuevos:
            try:
                vp = self.window()
                if hasattr(vp, '_verificar_y_limpiar_vencidos'):
                    vp._verificar_y_limpiar_vencidos()
            except Exception:
                pass

    # ──────────────────────────────────────────────────────────────────────────
    # CARGA DE DATOS
    # ──────────────────────────────────────────────────────────────────────────

    def _notificar_cambios_globales(self):
        vp = self.window()
        if hasattr(vp, 'notificar_cambios'):
            vp.notificar_cambios(["PRESUPUESTOS", "STOCK"])
        else:
            self.recargar()

    def recargar(self):
        kpis = qp.obtener_kpis_presupuestos(self.conn)
        self._mk_total.set_valor(str(kpis["total"]))
        self._mk_activos.set_valor(str(kpis["activos"]))
        self._mk_vencidos.set_valor(str(kpis["vencidos"]))
        self._mk_anulados.set_valor(str(kpis["anulados"]))
        
        res = qp.obtener_presupuestos_paginados(
            self.conn,
            filtro=self._filtro_texto,
            estado=self._estado_actual,
            fecha_desde=None,
            fecha_hasta=None,
            pagina=self._pagina_actual,
            por_pagina=self._por_pagina
        )
        
        self._total_paginas = res["total_paginas"]
        self._lbl_info_pag.setText(f"{res['total_filas']} presupuestos en total")
        self._lbl_pag_actual.setText(f"Pág. {self._pagina_actual} de {max(1, self._total_paginas)}")
        
        self._btn_prev.setEnabled(self._pagina_actual > 1)
        self._btn_next.setEnabled(self._pagina_actual < self._total_paginas)
        
        self._tabla.blockSignals(True)
        self._tabla.setUpdatesEnabled(False)
        self._tabla.setRowCount(0)
        self._lista_activos.clear()
        
        id_sel_encontrado = False
        fila_seleccionar = -1
        
        for i, row in enumerate(res["filas"]):
            self._tabla.insertRow(i)
            
            it_num = QTableWidgetItem(row["numero_interno"])
            it_num.setData(Qt.ItemDataRole.UserRole, row["id_documento"])
            it_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            it_cli = QTableWidgetItem(f"{row['cliente']}\n{row['cant_items']} ítems")
            it_cli.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            # Fecha con hora
            fecha_str = row["fecha_emision"]
            if fecha_str and len(fecha_str) >= 16:
                fecha_fmt = f"{fecha_str[8:10]}/{fecha_str[5:7]}/{fecha_str[:4]}\n{fecha_str[11:16]} hs"
            elif fecha_str and len(fecha_str) >= 10:
                fecha_fmt = f"{fecha_str[8:10]}/{fecha_str[5:7]}/{fecha_str[:4]}"
            else:
                fecha_fmt = ""
            it_fecha = QTableWidgetItem(fecha_fmt)
            it_fecha.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            st = row["estado"]
            
            # Validez (Custom Widget)
            w_val = QWidget()
            ly_val = QVBoxLayout(w_val)
            ly_val.setContentsMargins(4, 2, 4, 2)
            ly_val.setSpacing(2)
            ly_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            fecha_venc_str = row["fecha_vencimiento"]
            venc_txt = f"{fecha_venc_str[8:10]}/{fecha_venc_str[5:7]}/{fecha_venc_str[:4]} {fecha_venc_str[11:16]} hs" if fecha_venc_str and len(fecha_venc_str) >= 16 else "—"
            lbl_val_fecha = QLabel(venc_txt)
            lbl_val_fecha.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px;")
            lbl_val_fecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lbl_val_timer = QLabel("")
            lbl_val_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if st == "ACTIVO":
                lbl_val_timer.setText("Calculando...")
                self._lista_activos.append({
                    "fila": i,
                    "vencimiento": row["fecha_vencimiento"],
                    "id_documento": row["id_documento"],
                    "lbl_timer": lbl_val_timer
                })
            else:
                val_txt = "Vencido" if st == "VENCIDO" else "—"
                lbl_val_timer.setText(val_txt)
                if st == "VENCIDO": 
                    lbl_val_timer.setStyleSheet(f"color: #991b1b; font-weight: 800; font-size: 12px; background-color: #fee2e2; border-radius: 4px; padding: 2px 6px;")
                elif st == "ANULADO" or st == "CONFIRMADO":
                    lbl_val_timer.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-weight: bold; font-size: 12px;")
            
            ly_val.addWidget(lbl_val_fecha)
            ly_val.addWidget(lbl_val_timer)
            
            it_tot = QTableWidgetItem(f"$ {_fmt_moneda(row['total_final'])}")
            it_tot.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Estado (Insignia)
            w_est = QWidget()
            ly_est = QHBoxLayout(w_est)
            ly_est.setContentsMargins(4, 2, 4, 2)
            ly_est.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_est = QLabel(st)
            lbl_est.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # lbl_est.setFixedHeight(24) removed to prevent text cutoff
            
            if st == "ACTIVO":
                lbl_est.setStyleSheet("background-color: #dcfce7; color: #166534; border-radius: 12px; padding: 4px 10px; font-size: 11px; font-weight: 800; border: none;")
            elif st == "VENCIDO":
                lbl_est.setStyleSheet("background-color: #fee2e2; color: #991b1b; border-radius: 12px; padding: 4px 10px; font-size: 11px; font-weight: 800; border: none;")
            elif st == "CONFIRMADO":
                lbl_est.setStyleSheet(f"background-color: {COLOR_PRIMARY}20; color: {COLOR_PRIMARY}; border-radius: 12px; padding: 4px 10px; font-size: 11px; font-weight: 800; border: none;")
            elif st == "ANULADO":
                lbl_est.setStyleSheet("background-color: #f1f5f9; color: #475569; border-radius: 12px; padding: 4px 10px; font-size: 11px; font-weight: 800; border: none;")
            else:
                lbl_est.setStyleSheet("background-color: #f1f5f9; color: #475569; border-radius: 12px; padding: 4px 10px; font-size: 11px; font-weight: 800; border: none;")
            
            ly_est.addWidget(lbl_est)
            
            # Estado: solo widget, NO item de texto para evitar superposición
            # El setCellWidget reemplaza la celda correctamente
                
            # Acciones
            w_acc = _CeldaAcciones(row["id_documento"], estado=st)
            w_acc.ver_solicitado.connect(self._abrir_modal_detalle)
            w_acc.editar_solicitado.connect(self._editar_presupuesto)
            w_acc.preview_solicitado.connect(self._abrir_vista_previa)
            w_acc.pdf_solicitado.connect(self._generar_pdf)
            w_acc.confirmar_solicitado.connect(self._confirmar_como_venta)
            w_acc.anular_solicitado.connect(self._anular_presupuesto)
            
            self._tabla.setItem(i, 0, it_num)
            self._tabla.setItem(i, 1, it_cli)
            self._tabla.setItem(i, 2, it_fecha)
            self._tabla.setItem(i, 3, QTableWidgetItem("")) # Placeholder para w_val
            self._tabla.setItem(i, 4, it_tot)
            self._tabla.setItem(i, 5, QTableWidgetItem("")) # Placeholder para w_est
            self._tabla.setItem(i, 6, QTableWidgetItem("")) # Placeholder para w_acc
            self._tabla.setCellWidget(i, 3, w_val)
            self._tabla.setCellWidget(i, 5, w_est)
            self._tabla.setCellWidget(i, 6, w_acc)
            
            if self._id_seleccionado == row["id_documento"]:
                id_sel_encontrado = True
                fila_seleccionar = i
                
        # Sincronizar validez inicial
        self._on_timer_validez_tick()
                
        if id_sel_encontrado and fila_seleccionar >= 0:
            self._tabla.selectRow(fila_seleccionar)
            # Forzar actualización del panel porque signals están bloqueadas
            self._panel_detalle.cargar(self.conn, self._id_seleccionado)
        else:
            self._id_seleccionado = None
            self._panel_detalle.hide()
            self._panel_vacio.show()
            
        self._tabla.setUpdatesEnabled(True)
        self._tabla.blockSignals(False)
