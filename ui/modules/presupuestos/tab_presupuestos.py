"""
ui/modules/presupuestos/tab_presupuestos.py — Pestaña Principal de Presupuestos
"""
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSplitter, QScrollArea, QComboBox, QMessageBox,
    QGridLayout, QDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QCursor

from ui.core.theme import (
    COLOR_PRIMARY, COLOR_BG, COLOR_CARD_BG, COLOR_TEXT_MAIN,
    COLOR_TEXT_SEC, COLOR_BORDER, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from ui.core.modal import DialogoModalIntegrado
from ui.modules.ventas.tab_ventas import PestanaNuevaVenta
from db import queries_presupuestos as qp

def _fmt_moneda(valor: float) -> str:
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
            
        self.setWindowTitle(f"Presupuesto {det['numero_interno']}")
        self.setMinimumWidth(750)
        
        ly = QVBoxLayout(self)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(16)
        
        # 1. Cabecera e Info del Cliente
        f_top = QFrame()
        f_top.setStyleSheet(f"background-color: {COLOR_BG}; border-radius: 8px; border: 1px solid {COLOR_BORDER};")
        ly_top = QGridLayout(f_top)
        ly_top.setContentsMargins(16, 16, 16, 16)
        ly_top.setSpacing(12)
        
        lbl_cli = QLabel(det['cliente']['nombre_completo'])
        lbl_cli.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_TEXT_MAIN}; border: none;")
        ly_top.addWidget(lbl_cli, 0, 0, 1, 2)
        
        ly_top.addWidget(QLabel(f"<b>CUIT/DNI:</b> {det['cliente']['cuit_dni'] or '—'}"), 1, 0)
        ly_top.addWidget(QLabel(f"<b>Teléfono:</b> {det['cliente']['telefono'] or '—'}"), 1, 1)
        
        ly_top.addWidget(QLabel(f"<b>Emisión:</b> {det['fecha_emision'][:10]}"), 2, 0)
        ly_top.addWidget(QLabel(f"<b>Vencimiento:</b> {det['fecha_vencimiento'][:16]}"), 2, 1)
        
        ly_top.addWidget(QLabel(f"<b>Estado:</b> {det['estado']}"), 3, 0)
        ly_top.addWidget(QLabel(f"<b>Cond. IVA:</b> {det['cliente']['condicion_iva']}"), 3, 1)
        
        ly.addWidget(f_top)
        
        # 2. Tabla de Detalles
        tabla = QTableWidget(0, 4)
        tabla.setHorizontalHeaderLabels(["Producto", "Cant", "P. Unitario", "Subtotal"])
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tabla.setShowGrid(True)
        tabla.verticalHeader().setVisible(False)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla.setStyleSheet(f"""
            QTableWidget {{ border: 1px solid {COLOR_BORDER}; border-radius: 6px; background: {COLOR_CARD_BG}; }}
            QHeaderView::section {{ background-color: {COLOR_BG}; font-weight: bold; color: {COLOR_TEXT_SEC}; border: none; border-bottom: 1px solid {COLOR_BORDER}; padding: 6px; }}
            QTableWidget::item {{ padding: 6px; border-bottom: 1px solid #f1f5f9; color: {COLOR_TEXT_MAIN}; }}
        """)
        
        for i, item in enumerate(det['detalles']):
            tabla.insertRow(i)
            tabla.setItem(i, 0, QTableWidgetItem(f"{item['codigo_producto']} - {item['descripcion']}"))
            tabla.setItem(i, 1, QTableWidgetItem(f"{item['cantidad_unidad_venta']} {item['unidad_venta']}"))
            
            it_pu = QTableWidgetItem(_fmt_moneda(item['precio_unitario']))
            it_pu.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tabla.setItem(i, 2, it_pu)
            
            it_sub = QTableWidgetItem(_fmt_moneda(item['subtotal']))
            it_sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tabla.setItem(i, 3, it_sub)
            
        ly.addWidget(tabla, stretch=1)
        
        # 3. Observaciones y Totales
        f_bot = QHBoxLayout()
        
        lbl_obs = QLabel(f"<b>Observaciones:</b><br>{det['observaciones'] or 'Sin observaciones'}")
        lbl_obs.setWordWrap(True)
        lbl_obs.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px;")
        f_bot.addWidget(lbl_obs, stretch=1)
        
        f_tots = QFrame()
        f_tots.setStyleSheet(f"background-color: {COLOR_BG}; border-radius: 6px; padding: 12px; border: 1px solid {COLOR_BORDER};")
        ly_tots = QVBoxLayout(f_tots)
        
        if det['subtotal_bruto'] != det['total_final']:
            ly_tots.addWidget(QLabel(f"Subtotal: {_fmt_moneda(det['subtotal_bruto'])}"))
        if det['total_descuento'] > 0:
            ly_tots.addWidget(QLabel(f"Descuento: -{_fmt_moneda(det['total_descuento'])}"))
        if det['iva_monto'] > 0:
            ly_tots.addWidget(QLabel(f"IVA: {_fmt_moneda(det['iva_monto'])}"))
            
        lbl_tot = QLabel(f"TOTAL: {_fmt_moneda(det['total_final'])}")
        lbl_tot.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {COLOR_PRIMARY};")
        ly_tots.addWidget(lbl_tot)
        
        f_bot.addWidget(f_tots)
        ly.addLayout(f_bot)

class DialogoNuevoPresupuesto(DialogoModalIntegrado):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle("Crear Nuevo Presupuesto")
        # El widget de venta es ancho, necesitamos un modal grande
        self.setMinimumWidth(1100)
        self.setMinimumHeight(750)
        
        ly = QVBoxLayout(self)
        ly.setContentsMargins(0, 0, 0, 0)
        
        self.pestana_venta = PestanaNuevaVenta(self.conn, is_presupuesto=True)
        # Quitar el color de fondo para integrarlo bien al modal
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
        layout.setSpacing(2)

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
                border-radius: 8px;
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

class _PanelVacio(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
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
    anular_solicitado = pyqtSignal(int)
    confirmar_solicitado = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"QScrollArea {{ border: none; background-color: {COLOR_CARD_BG}; }}")
        self._id_actual = None
        
        self._contenido = QWidget()
        self._contenido.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: none;")
        self._layout = QVBoxLayout(self._contenido)
        self._layout.setContentsMargins(14, 14, 14, 14)
        self._layout.setSpacing(10)
        
        # Titulo y Cliente
        self._lbl_num = QLabel("—")
        self._lbl_num.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {COLOR_TEXT_MAIN};")
        self._layout.addWidget(self._lbl_num)
        
        self._lbl_cliente = QLabel("—")
        self._lbl_cliente.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        self._lbl_cliente.setWordWrap(True)
        self._layout.addWidget(self._lbl_cliente)
        
        # Info secundaria
        self._lbl_fechas = QLabel("—")
        self._lbl_fechas.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SEC};")
        self._layout.addWidget(self._lbl_fechas)
        
        self._lbl_validez = QLabel("—")
        self._lbl_validez.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {COLOR_PRIMARY};")
        self._layout.addWidget(self._lbl_validez)
        
        self._lbl_items = QLabel("—")
        self._lbl_items.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SEC};")
        self._layout.addWidget(self._lbl_items)
        
        self._layout.addSpacing(10)
        
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
        self._btn_ver = QPushButton("Ver detalle completo")
        self._btn_ver.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_ver.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; padding: 8px; border-radius: 6px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        self._btn_ver.clicked.connect(lambda: self.ver_detalle_solicitado.emit(self._id_actual) if self._id_actual else None)
        
        self._btn_editar = QPushButton("Editar presupuesto")
        self._btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_editar.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; padding: 8px; border-radius: 6px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        
        self._btn_pdf = QPushButton("Generar PDF")
        self._btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_pdf.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; padding: 8px; border-radius: 6px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        self._btn_pdf.clicked.connect(lambda: QMessageBox.information(self, "PDF", "Funcionalidad pendiente."))
        
        self._btn_confirmar = QPushButton("Confirmar como Venta")
        self._btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_confirmar.setStyleSheet(f"background-color: {COLOR_PRIMARY}; border: 1px solid {COLOR_PRIMARY}; padding: 8px; border-radius: 6px; font-weight: bold; color: white;")
        self._btn_confirmar.clicked.connect(lambda: self.confirmar_solicitado.emit(self._id_actual) if self._id_actual else None)
        
        self._btn_anular = QPushButton("Anular presupuesto")
        self._btn_anular.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_anular.setStyleSheet(f"background-color: #fee2e2; border: 1px solid #fca5a5; padding: 8px; border-radius: 6px; font-weight: bold; color: {COLOR_DANGER};")
        self._btn_anular.clicked.connect(lambda: self.anular_solicitado.emit(self._id_actual) if self._id_actual else None)
        
        self._layout.addWidget(self._btn_ver)
        self._layout.addWidget(self._btn_editar)
        self._layout.addWidget(self._btn_confirmar)
        self._layout.addWidget(self._btn_pdf)
        self._layout.addWidget(self._btn_anular)
        
        self.setWidget(self._contenido)
        
    def cargar(self, conn, id_documento: int):
        self._id_actual = id_documento
        det = qp.obtener_detalle_presupuesto(conn, id_documento)
        if not det: return
        
        self._lbl_num.setText(f"{det['numero_interno']} ({det['estado']})")
        self._lbl_cliente.setText(det['cliente']['nombre_completo'])
        self._lbl_fechas.setText(f"Emisión: {det['fecha_emision'][:10]}")
        self._lbl_validez.setText(f"Validez: Calculando...") # Será actualizado por el QTimer si es ACTIVO
        self._lbl_items.setText(f"Ítems: {len(det['detalles'])}")
        self._lbl_total.setText(f"Total: {_fmt_moneda(det['total_final'])}")
        
        obs = det['observaciones']
        self._lbl_obs.setText(f"Notas: {obs}" if obs else "Sin observaciones.")
        
        self._btn_editar.setVisible(det['estado'] == 'ACTIVO')
        self._btn_confirmar.setVisible(det['estado'] == 'ACTIVO')
        self._btn_anular.setVisible(det['estado'] == 'ACTIVO')

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
        ly.setSpacing(14)

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
                padding: 8px 14px; border-radius: 6px; border: 1px solid {COLOR_BORDER};
            }}
            QPushButton.secundario:hover {{ background-color: {COLOR_BG}; }}
            QPushButton.pagina {{
                background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; font-size: 13px;
                padding: 5px 12px; border-radius: 5px; border: 1px solid {COLOR_BORDER}; min-width: 32px;
            }}
            QPushButton.pagina:hover {{ background-color: {COLOR_BG}; border-color: {COLOR_PRIMARY}; }}
            QPushButton.pagina:disabled {{ color: {COLOR_BORDER}; background-color: {COLOR_BG}; }}
            QTableWidget {{
                border: 1px solid {COLOR_BORDER}; border-radius: 8px; gridline-color: {COLOR_BORDER};
                background-color: {COLOR_CARD_BG}; outline: none; font-size: 13px;
            }}
            QHeaderView::section {{
                background-color: {COLOR_BG}; color: {COLOR_TEXT_SEC}; font-weight: 700; font-size: 12px;
                border: none; border-bottom: 1px solid {COLOR_BORDER}; padding: 10px 8px;
            }}
            QTableWidget::item {{ border-bottom: 1px solid #f1f5f9; padding: 4px 8px; color: {COLOR_TEXT_MAIN}; }}
            QTableWidget::item:selected {{ background-color: #ebf5ff; color: {COLOR_TEXT_MAIN}; }}
        """

    def _construir_encabezado(self) -> QHBoxLayout:
        ly = QHBoxLayout()
        info = QVBoxLayout()
        info.setSpacing(2)
        tit = QLabel("Presupuestos")
        tit.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {COLOR_TEXT_MAIN}; border: none;")
        sub = QLabel("Gestión y seguimiento de cotizaciones y compromisos de stock.")
        sub.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SEC}; border: none;")
        info.addWidget(tit)
        info.addWidget(sub)

        self._btn_nuevo = QPushButton("+ Nuevo Presupuesto")
        self._btn_nuevo.setProperty("class", "primario")
        self._btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_nuevo.clicked.connect(self._abrir_modal_nuevo_presupuesto)

        ly.addLayout(info)
        ly.addStretch()
        ly.addWidget(self._btn_nuevo, alignment=Qt.AlignmentFlag.AlignTop)
        return ly

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
        f.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
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
        self._tabla.setShowGrid(False)
        self._tabla.verticalHeader().setVisible(False)
        
        hdr = self._tabla.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self._tabla.itemSelectionChanged.connect(self._on_seleccion_cambiada)
        
        spl.addWidget(self._tabla)

        self._panel_vacio = _PanelVacio()
        self._panel_detalle = _PanelDetalle()
        self._panel_detalle.ver_detalle_solicitado.connect(self._abrir_modal_detalle)
        self._panel_detalle.anular_solicitado.connect(self._anular_presupuesto)
        self._panel_detalle.confirmar_solicitado.connect(self._confirmar_como_venta)
        self._panel_detalle.hide()

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
            
    def _on_seleccion_cambiada(self):
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
        dlg = DialogoNuevoPresupuesto(self.conn, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.recargar()

    def _anular_presupuesto(self, id_documento: int):
        det = qp.obtener_detalle_presupuesto(self.conn, id_documento)
        if not det or det['estado'] != 'ACTIVO':
            QMessageBox.warning(self, "Error", "El presupuesto no se puede anular.")
            return
            
        dlg = QMessageBox(self.window())
        dlg.setWindowTitle("Confirmar Anulación")
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setText(f"¿Estás seguro de anular el presupuesto <b>{det['numero_interno']}</b>?")
        dlg.setInformativeText(f"Cliente: <b>{det['cliente']['nombre_completo']}</b><br><br>Al anularlo, se <b>liberará todo el stock comprometido</b> de forma inmediata. Esta acción no se puede deshacer y no eliminará el registro histórico.")
        dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        dlg.button(QMessageBox.StandardButton.Yes).setText("Sí, anular")
        dlg.button(QMessageBox.StandardButton.Cancel).setText("Cancelar")
        
        if dlg.exec() == QMessageBox.StandardButton.Yes:
            try:
                qp.anular_presupuesto(self.conn, id_documento)
                # Notificar a la ventana principal para actualizar ATP global si es necesario
                # Aunque ya refrescamos aquí, podemos emitir una señal o llamar a un método seguro
                self.recargar()
                QMessageBox.information(self, "Éxito", f"Presupuesto {det['numero_interno']} anulado correctamente.")
                
                # Intentar recargar la pestaña de stock usando una llamada segura al parent
                try:
                    vp = self.window()
                    if hasattr(vp, 'pestana_stock'):
                        vp.pestana_stock.cargar_datos()
                    if hasattr(vp, 'vista_ventas_temp'):
                        vp.vista_ventas_temp.cargar_catalogo_memoria()
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un error al anular:\n{e}")

    def _confirmar_como_venta(self, id_documento: int):
        det = qp.obtener_detalle_presupuesto(self.conn, id_documento)
        if not det or det['estado'] != 'ACTIVO':
            QMessageBox.warning(self, "Error", "El presupuesto no se puede confirmar.")
            return
            
        dlg = QMessageBox(self.window())
        dlg.setWindowTitle("Confirmar como Venta")
        dlg.setIcon(QMessageBox.Icon.Question)
        
        cant_prods = len(det['detalles'])
        
        dlg.setText(f"¿Deseas confirmar el presupuesto <b>{det['numero_interno']}</b> como venta real?")
        
        total_formateado = f"$ {det['total_final']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        dlg.setInformativeText(
            f"Cliente: <b>{det['cliente']['nombre_completo']}</b><br>"
            f"Total: <b>{total_formateado}</b><br>"
            f"Productos: <b>{cant_prods} ítem(s)</b><br><br>"
            f"⚠️ Esta acción es irreversible. Consumirá el material comprometido y registrará la salida física del inventario de forma inmediata."
        )
        dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        dlg.button(QMessageBox.StandardButton.Yes).setText("Confirmar Venta")
        dlg.button(QMessageBox.StandardButton.Cancel).setText("Cancelar")
        
        if dlg.exec() == QMessageBox.StandardButton.Yes:
            try:
                num_venta = qp.confirmar_presupuesto(self.conn, id_documento)
                self.recargar()
                
                try:
                    vp = self.window()
                    if hasattr(vp, 'pestana_stock'):
                        vp.pestana_stock.cargar_datos()
                    if hasattr(vp, 'vista_ventas_temp'):
                        vp.vista_ventas_temp.cargar_catalogo_memoria()
                except Exception:
                    pass
                
                # Lanzar modal de éxito usando DialogoVentaExitosa y pasando el origen extra
                from ui.modules.ventas.tab_ventas import DialogoVentaExitosa
                from datetime import datetime
                cant_unidades = sum(d['cantidad_unidad_venta'] for d in det['detalles'])
                
                cli_origen = f"{det['cliente']['nombre_completo']}\n(Origen: Presupuesto {det['numero_interno']})"
                
                exito_dlg = DialogoVentaExitosa(
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
        for item in self._lista_activos:
            venc_str = item["vencimiento"]
            if not venc_str: continue
            
            try:
                venc_dt = datetime.datetime.strptime(venc_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    venc_dt = datetime.datetime.strptime(venc_str, "%Y-%m-%d")
                except ValueError:
                    continue
                    
            if venc_dt <= ahora:
                texto = "Vencido"
            else:
                diff = venc_dt - ahora
                segundos = int(diff.total_seconds())
                dias, res = divmod(segundos, 86400)
                horas, res = divmod(res, 3600)
                mins, secs = divmod(res, 60)
                if dias > 0:
                    texto = f"{dias} d {horas:02d}:{mins:02d}:{secs:02d}"
                else:
                    texto = f"{horas:02d}:{mins:02d}:{secs:02d}"
                    
            # Actualizar celda sin romper la selección
            it = self._tabla.item(item["fila"], 3)
            if it and it.text() != texto:
                it.setText(texto)
                if texto == "Vencido":
                    it.setForeground(QColor(COLOR_DANGER))
                    
            # Sincronizar panel lateral si el item está seleccionado
            if self._id_seleccionado == item["id_documento"]:
                self._panel_detalle._lbl_validez.setText(f"Validez: {texto}")

    # ──────────────────────────────────────────────────────────────────────────
    # CARGA DE DATOS
    # ──────────────────────────────────────────────────────────────────────────

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
        self._tabla.setRowCount(0)
        self._lista_activos.clear()
        
        id_sel_encontrado = False
        fila_seleccionar = -1
        
        for i, row in enumerate(res["filas"]):
            self._tabla.insertRow(i)
            
            it_num = QTableWidgetItem(row["numero_interno"])
            it_num.setData(Qt.ItemDataRole.UserRole, row["id_documento"])
            
            it_cli = QTableWidgetItem(row["cliente"])
            it_fecha = QTableWidgetItem(row["fecha_emision"][:10] if row["fecha_emision"] else "")
            
            st = row["estado"]
            
            # Validez
            if st == "ACTIVO":
                self._lista_activos.append({
                    "fila": i,
                    "vencimiento": row["fecha_vencimiento"],
                    "id_documento": row["id_documento"]
                })
                it_val = QTableWidgetItem("Calculando...")
            else:
                val_txt = "Vencido" if st == "VENCIDO" else "—"
                it_val = QTableWidgetItem(val_txt)
                if st == "VENCIDO": it_val.setForeground(QColor(COLOR_DANGER))
                elif st == "ANULADO": it_val.setForeground(QColor(COLOR_TEXT_SEC))
            
            it_tot = QTableWidgetItem(_fmt_moneda(row["total_final"]))
            it_tot.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            it_est = QTableWidgetItem(st)
            it_est.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if st == "ACTIVO":
                it_est.setForeground(QColor(COLOR_SUCCESS))
            elif st == "VENCIDO":
                it_est.setForeground(QColor(COLOR_DANGER))
            elif st == "ANULADO":
                it_est.setForeground(QColor(COLOR_TEXT_SEC))
            elif st == "CONFIRMADO":
                it_est.setForeground(QColor(COLOR_PRIMARY))
                
            it_acc = QTableWidgetItem("...")
            it_acc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self._tabla.setItem(i, 0, it_num)
            self._tabla.setItem(i, 1, it_cli)
            self._tabla.setItem(i, 2, it_fecha)
            self._tabla.setItem(i, 3, it_val)
            self._tabla.setItem(i, 4, it_tot)
            self._tabla.setItem(i, 5, it_est)
            self._tabla.setItem(i, 6, it_acc)
            
            if self._id_seleccionado == row["id_documento"]:
                id_sel_encontrado = True
                fila_seleccionar = i
                
        # Sincronizar validez inicial
        self._on_timer_validez_tick()
                
        if id_sel_encontrado and fila_seleccionar >= 0:
            self._tabla.selectRow(fila_seleccionar)
        else:
            self._id_seleccionado = None
            self._panel_detalle.hide()
            self._panel_vacio.show()
            
        self._tabla.blockSignals(False)
