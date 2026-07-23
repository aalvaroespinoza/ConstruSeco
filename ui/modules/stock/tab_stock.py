import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QFrame, QDialog, QFormLayout, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QSize
from datetime import datetime
from PyQt6.QtGui import QColor, QFont, QCursor, QAction, QBrush, QPixmap

from db.queries import obtener_stocks_todos, obtener_metricas_globales, obtener_productos_frecuentes, UNIDADES_PERMITIDAS
from db.queries_stock import migrar_esquema_stock
from ui.modules.stock.dialogs_stock import (
    DialogoAgregarProducto, DialogoEditarProducto,
    DialogoStockMinimo, DialogoModificarStock,
    VistaDetalleProducto
)
from ui.modules.stock.excel_stock import (
    DialogoImportarExcel, exportar_inventario_excel, generar_plantilla_excel
)
from ui.modules.stock.ajustes_stock import (
    DialogoConfiguracionGeneral, DialogoHistorialMovimientos, DialogoVisualizacionInventario
)
from PyQt6.QtCore import QSettings

from ui.core.theme import (
    COLOR_PRIMARY, COLOR_BG, COLOR_CARD_BG, COLOR_TEXT_MAIN,
    COLOR_TEXT_SEC, COLOR_BORDER, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)


from PyQt6.QtCore import pyqtSignal

class TarjetaMetrica(QFrame):
    clicked_tarjeta = pyqtSignal(object)
    
    def __init__(self, titulo, valor, color_borde=COLOR_PRIMARY):
        super().__init__()
        self.setStyleSheet(f"""
            TarjetaMetrica {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                border-left: 4px solid {color_borde};
            }}
            TarjetaMetrica:hover {{
                background-color: #f8fafc;
            }}
        """)
        self.setMinimumWidth(180)
        self.setFixedHeight(84)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.titulo_texto = titulo
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(16)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 13px; font-weight: 800;")
        
        self.lbl_valor = QLabel(str(valor))
        self.lbl_valor.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 22px; font-weight: 900; letter-spacing: -0.5px;")
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(self.lbl_valor)
        layout.addStretch()

    def set_valor(self, valor):
        self.lbl_valor.setText(str(valor))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked_tarjeta.emit(self)

class TarjetaFrecuente(QFrame):
    clicked_codigo = pyqtSignal(str)
    
    def __init__(self, producto):
        super().__init__()
        self.setStyleSheet(f"""
            TarjetaFrecuente {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
            }}
            TarjetaFrecuente:hover {{
                border: 1px solid {COLOR_PRIMARY};
                background-color: #f8fafc;
            }}
        """)
        self.setFixedSize(240, 90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.codigo = producto['codigo']
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Placeholder para imagen
        frame_img = QFrame()
        frame_img.setFixedSize(50, 50)
        frame_img.setStyleSheet(f"background-color: {COLOR_BG}; border-radius: 6px; border: 1px solid {COLOR_BORDER};")
        ly_img = QVBoxLayout(frame_img)
        ly_img.setContentsMargins(0,0,0,0)
        lbl_icon = QLabel("📦")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 20px;")
        ly_img.addWidget(lbl_icon)
        
        layout.addWidget(frame_img)
        
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0,0,0,0)
        info_layout.setSpacing(2)
        
        lbl_desc = QLabel(producto["descripcion"])
        lbl_desc.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 13px; font-weight: bold; border: none;")
        
        lbl_cod = QLabel(f"Cód: {self.codigo}")
        lbl_cod.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px; border: none;")
        
        atp = producto["atp"]
        unidad = producto["unidad_base"]
        stk_min = producto["stock_minimo"]
        
        lbl_stock = QLabel(f"Disp: {atp:g} {unidad}")
        
        color_stock = COLOR_SUCCESS
        if atp <= 0:
            color_stock = COLOR_DANGER
        elif stk_min > 0 and atp <= stk_min:
            color_stock = COLOR_WARNING
            
        lbl_stock.setStyleSheet(f"color: {color_stock}; font-size: 12px; font-weight: bold; border: none;")
        
        info_layout.addWidget(lbl_desc)
        info_layout.addWidget(lbl_cod)
        info_layout.addWidget(lbl_stock)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked_codigo.emit(self.codigo)


class PestanaStock(QWidget):
    def __init__(self, conexion_db):
        super().__init__()
        self.conn = conexion_db
        migrar_esquema_stock(self.conn)
        self.datos_catalogo = []
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        self.setStyleSheet(f"""
            PestanaStock, QWidget#main_container {{
                background-color: {COLOR_BG};
            }}
            /* Estilos de botones */
            QPushButton.primario {{
                background-color: {COLOR_PRIMARY}; 
                color: white; 
                font-weight: bold;
                padding: 6px 14px; 
                border-radius: 6px; 
                font-size: 12px;
                border: none;
            }}
            QPushButton.primario:hover {{ background-color: #1d4ed8; }}
            
            QPushButton.secundario {{
                background-color: {COLOR_CARD_BG}; 
                color: {COLOR_TEXT_MAIN}; 
                font-weight: bold;
                padding: 6px 14px; 
                border-radius: 6px; 
                font-size: 12px;
                border: 1px solid {COLOR_BORDER};
            }}
            QPushButton.secundario:hover {{ background-color: {COLOR_BG}; }}
            
            /* Inputs */
            QLineEdit {{
                padding: 10px 12px;
                font-size: 13px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                background-color: {COLOR_CARD_BG};
                color: {COLOR_TEXT_MAIN};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_PRIMARY};
            }}
            
            QComboBox {{
                padding: 10px 12px;
                font-size: 13px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                background-color: {COLOR_CARD_BG};
                color: {COLOR_TEXT_MAIN};
            }}
            
            /* Tabla */
            QTableWidget {{
                border: 1px solid {COLOR_BORDER}; border-radius: 6px;
                gridline-color: {COLOR_BORDER};
                background-color: {COLOR_CARD_BG}; outline: none; font-size: 13px;
                color: {COLOR_TEXT_MAIN};
            }}
            QHeaderView::section {{
                background-color: {COLOR_BG}; color: {COLOR_TEXT_SEC};
                font-weight: 700; font-size: 12px;
                border: none; border-bottom: 1px solid {COLOR_BORDER}; padding: 10px 8px;
            }}
            QTableWidget::item {{
                border-bottom: 1px solid #f1f5f9;
                padding: 4px 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {COLOR_PRIMARY}; color: white;
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 1. ENCABEZADO
        header_layout = QHBoxLayout()
        titles_layout = QVBoxLayout()
        titles_layout.setSpacing(4)
        
        lbl_titulo = QLabel("Control de Stock")
        lbl_titulo.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {COLOR_TEXT_MAIN};")
        lbl_subtitulo = QLabel("Inventario, disponibilidad y métricas")
        lbl_subtitulo.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_SEC};")
        
        titles_layout.addWidget(lbl_titulo)
        titles_layout.addWidget(lbl_subtitulo)
        
        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.setToolTip("Forzar recarga de datos")
        btn_actualizar.setProperty("class", "secundario")
        btn_actualizar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_actualizar.clicked.connect(self.actualizar_vista)
        
        btn_ayuda = QPushButton("ⓘ Ayuda")
        btn_ayuda.setProperty("class", "secundario")
        btn_ayuda.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ayuda.clicked.connect(self._mostrar_ayuda)
        
        btn_ajustes = QPushButton("⚙️ Ajustes")
        btn_ajustes.setProperty("class", "secundario")
        btn_ajustes.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ajustes.clicked.connect(self.abrir_configuracion_general)

        btn_historial = QPushButton("📜 Historial")
        btn_historial.setProperty("class", "secundario")
        btn_historial.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_historial.clicked.connect(self.abrir_historial_movimientos)

        btn_excel = QPushButton("📊 Excel ▾")
        btn_excel.setProperty("class", "secundario")
        btn_excel.setCursor(Qt.CursorShape.PointingHandCursor)
        menu_excel = QMenu(btn_excel)
        menu_excel.setStyleSheet("QMenu { background-color: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px; } QMenu::item { padding: 8px 16px; border-radius: 4px; } QMenu::item:selected { background-color: #f1f5f9; }")
        menu_excel.addAction("📥 Importar...").triggered.connect(self.abrir_importar_excel)
        menu_excel.addAction("📤 Exportar...").triggered.connect(lambda: exportar_inventario_excel(self.conn, self))
        btn_excel.setMenu(menu_excel)

        btn_agregar = QPushButton("➕ Nuevo Producto")
        btn_agregar.setProperty("class", "primario")
        btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_agregar.clicked.connect(self.abrir_formulario_alta)
        
        header_layout.addLayout(titles_layout)
        header_layout.addStretch()
        header_layout.addWidget(btn_ayuda)
        header_layout.addWidget(btn_actualizar)
        header_layout.addWidget(btn_ajustes)
        header_layout.addWidget(btn_historial)
        header_layout.addWidget(btn_excel)
        header_layout.addWidget(btn_agregar)
        
        main_layout.addLayout(header_layout)
        
        # 2. PANELES SUPERIORES (Resumen, Alertas, Frecuentes)
        top_panels_layout = QHBoxLayout()
        top_panels_layout.setSpacing(16)
        
        # Panel Resumen
        self.panel_resumen = QFrame()
        self.panel_resumen.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG}; 
                border: 1px solid {COLOR_BORDER}; 
                border-radius: 6px;
                border-left: 4px solid {COLOR_PRIMARY};
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        ly_resumen = QVBoxLayout(self.panel_resumen)
        ly_resumen.setContentsMargins(16, 14, 16, 14)
        ly_resumen.setSpacing(12)
        
        lbl_res_tit = QLabel("Resumen General")
        lbl_res_tit.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: bold; font-size: 14px;")
        ly_resumen.addWidget(lbl_res_tit)
        
        # Contenedor para alinear los datos
        ly_datos = QVBoxLayout()
        ly_datos.setSpacing(8)
        
        # Fila Total Productos
        row_tot = QHBoxLayout()
        lbl_tot_tit = QLabel("Total de Productos:")
        lbl_tot_tit.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 13px;")
        self.lbl_res_total = QLabel("0")
        self.lbl_res_total.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: 900; font-size: 15px;")
        row_tot.addWidget(lbl_tot_tit)
        row_tot.addStretch()
        row_tot.addWidget(self.lbl_res_total)
        ly_datos.addLayout(row_tot)
        
        # Fila Productos con Stock
        row_stk = QHBoxLayout()
        lbl_stk_tit = QLabel("Productos con Stock:")
        lbl_stk_tit.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 13px;")
        self.lbl_res_stock = QLabel("0")
        self.lbl_res_stock.setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: 900; font-size: 15px;")
        row_stk.addWidget(lbl_stk_tit)
        row_stk.addStretch()
        row_stk.addWidget(self.lbl_res_stock)
        ly_datos.addLayout(row_stk)
        
        # Fila Valor Inventario
        row_val = QHBoxLayout()
        lbl_val_tit = QLabel("Valor del Inventario:")
        lbl_val_tit.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 13px;")
        self.lbl_res_valor = QLabel("$0.00")
        self.lbl_res_valor.setStyleSheet(f"color: {COLOR_PRIMARY}; font-weight: 900; font-size: 16px;")
        row_val.addWidget(lbl_val_tit)
        row_val.addStretch()
        row_val.addWidget(self.lbl_res_valor)
        ly_datos.addLayout(row_val)
        
        ly_resumen.addLayout(ly_datos)
        ly_resumen.addStretch()
        
        self.lbl_res_act = QLabel(f"Últ. actualización: {datetime.now().strftime('%H:%M')}")
        self.lbl_res_act.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px;")
        ly_resumen.addWidget(self.lbl_res_act, 0, Qt.AlignmentFlag.AlignRight)
            
        # Panel Alertas
        self.panel_alertas = QFrame()
        self.panel_alertas.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        ly_alertas = QVBoxLayout(self.panel_alertas)
        ly_alertas.setContentsMargins(16, 12, 16, 12)
        ly_alertas.setSpacing(8)
        head_alertas = QHBoxLayout()
        lbl_al_tit = QLabel("⚠️ Alertas de Inventario")
        lbl_al_tit.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: bold; font-size: 14px; border: none;")
        btn_ver_alertas = QPushButton("Ver alertas")
        btn_ver_alertas.setStyleSheet(f"color: {COLOR_PRIMARY}; background: transparent; border: none; font-size: 12px; font-weight: bold;")
        btn_ver_alertas.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ver_alertas.clicked.connect(self.abrir_alertas_inventario)
        head_alertas.addWidget(lbl_al_tit)
        head_alertas.addStretch()
        head_alertas.addWidget(btn_ver_alertas)
        ly_alertas.addLayout(head_alertas)
        self.ly_items_alertas = QVBoxLayout()
        self.ly_items_alertas.setSpacing(4)
        ly_alertas.addLayout(self.ly_items_alertas)
        ly_alertas.addStretch()
        
        # Panel Frecuentes
        self.panel_frecuentes = QFrame()
        self.panel_frecuentes.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        ly_frecuentes = QVBoxLayout(self.panel_frecuentes)
        ly_frecuentes.setContentsMargins(16, 12, 16, 12)
        ly_frecuentes.setSpacing(8)
        head_frec = QHBoxLayout()
        lbl_fr_tit = QLabel("⭐ Productos Frecuentes")
        lbl_fr_tit.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: bold; font-size: 14px; border: none;")
        btn_ver_frec = QPushButton("Ver frecuentes")
        btn_ver_frec.setStyleSheet(f"color: {COLOR_PRIMARY}; background: transparent; border: none; font-size: 12px; font-weight: bold;")
        btn_ver_frec.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ver_frec.clicked.connect(self.abrir_frecuentes)
        head_frec.addWidget(lbl_fr_tit)
        head_frec.addStretch()
        head_frec.addWidget(btn_ver_frec)
        ly_frecuentes.addLayout(head_frec)
        self.ly_items_frecuentes = QVBoxLayout()
        self.ly_items_frecuentes.setSpacing(4)
        ly_frecuentes.addLayout(self.ly_items_frecuentes)
        ly_frecuentes.addStretch()
        
        top_panels_layout.addWidget(self.panel_resumen, 1)
        top_panels_layout.addWidget(self.panel_frecuentes, 2)
        top_panels_layout.addWidget(self.panel_alertas, 2)
        
        main_layout.addLayout(top_panels_layout)
        
        # 4. FILTROS Y BÚSQUEDA
        filtros_layout = QHBoxLayout()
        filtros_layout.setSpacing(12)
        
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍 Buscar producto por descripción o código...")
        self.input_buscar.setMinimumWidth(300)
        
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["Todos los Estados", "Disponible", "Stock Bajo", "Sin Stock", "Inactivo"])
        
        self.combo_unidad = QComboBox()
        self.combo_unidad.addItem("Todas las Unidades", userData=None)
        for val_bd, etiqueta in UNIDADES_PERMITIDAS:
            self.combo_unidad.addItem(etiqueta, userData=val_bd)
            
        self.combo_orden = QComboBox()
        self.combo_orden.addItems(["Ordenar por Descripción", "Mayor Stock", "Menor Stock"])
        
        filtros_layout.addWidget(self.input_buscar)
        filtros_layout.addWidget(self.combo_estado)
        filtros_layout.addWidget(self.combo_unidad)
        filtros_layout.addWidget(self.combo_orden)
        filtros_layout.addStretch()
        
        main_layout.addLayout(filtros_layout)
        
        # 5. TABLA PRINCIPAL - 11 columnas con miniatura
        self.tabla = QTableWidget(0, 11)
        self.tabla.setHorizontalHeaderLabels([
            "Código", "Foto", "Producto", "Unidad", "Stock Físico", "Comprometido", 
            "Disponible", "Stock Mínimo", "Precio", "Estado", "Acciones"
        ])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(48)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.setShowGrid(True)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(self.tabla.styleSheet() + """
            QTableWidget { alternate-background-color: #fafbfd; }
            QTableWidget::item:selected {
                  background-color: #2563eb;
                  color: white;
              }
        """)
        self.tabla.cellDoubleClicked.connect(self.on_tabla_double_click)
        self.tabla.itemSelectionChanged.connect(self._actualizar_colores_seleccion)
        
        # Implementar toggle de selección limpio y seguro
        _original_mouse_press = self.tabla.mousePressEvent
        def _custom_mouse_press(event):
            idx = self.tabla.indexAt(event.pos())
            if idx.isValid() and event.button() == Qt.MouseButton.LeftButton:
                # Evitar interferir con la columna de Acciones
                if idx.column() == 10:
                    _original_mouse_press(event)
                    return
                    
                selected_rows = [r.row() for r in self.tabla.selectionModel().selectedRows()]
                if idx.row() in selected_rows:
                    self.tabla.clearSelection()
                    self.tabla.setCurrentItem(None)
                    event.accept()
                    return
            _original_mouse_press(event)
        self.tabla.mousePressEvent = _custom_mouse_press
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Producto/Descripcion
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Img
        self.tabla.setColumnWidth(1, 52)

        # Configuración de columna Acciones
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(10, 90)
        item_acciones = self.tabla.horizontalHeaderItem(10)
        if item_acciones:
            item_acciones.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(self.tabla, stretch=1)
        
        # Conexiones de filtros
        self.input_buscar.textChanged.connect(self.aplicar_filtros)
        self.combo_estado.currentIndexChanged.connect(self.aplicar_filtros)
        self.combo_unidad.currentIndexChanged.connect(self.aplicar_filtros)
        self.combo_orden.currentIndexChanged.connect(self.aplicar_filtros)
        




    def actualizar_vista(self):
        """Coordina la recarga manual de toda la vista de stock, reutilizando la lógica principal."""
        self._notificar_cambios_globales()

    def _notificar_cambios_globales(self):
        vp = self.window()
        if hasattr(vp, 'notificar_cambios'):
            vp.notificar_cambios(["STOCK"])
        else:
            self.cargar_datos()

    def _mostrar_ayuda(self):
        from ui.modules.stock.dialogs_stock import DialogoAyudaStock
        dialogo = DialogoAyudaStock(self.window())
        dialogo.exec()

    def cargar_datos(self):
        # 1. Cargar métricas globales
        metricas = obtener_metricas_globales(self.conn)
        self.lbl_res_total.setText(str(metricas['total_productos']))
        valor = metricas["valor_inventario"]
        self.lbl_res_valor.setText(f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        con_stock = metricas["total_productos"] - metricas["sin_stock"]
        self.lbl_res_stock.setText(str(con_stock))
        self.lbl_res_act.setText(f"Últ. actualización: {datetime.now().strftime('%H:%M')}")
        
        # 3. Cargar catálogo completo
        self.datos_catalogo = obtener_stocks_todos(self.conn, incluir_inactivos=True)
        
        # 2. Cargar frecuentes
        while self.ly_items_frecuentes.count():
            item = self.ly_items_frecuentes.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        settings = QSettings("ConstrusecoPereyra", "StockConfig")
        limite = settings.value("freq_limit", 3, type=int)
        dias = settings.value("freq_days", 30, type=int)
        
        frecuentes = obtener_productos_frecuentes(self.conn, limite=limite, dias=dias)
        if frecuentes:
            for p in frecuentes[:3]: # Asegurar top 3
                # Mini layout for card
                w = QFrame()
                w.setStyleSheet("background-color: #f8fafc; border-radius: 6px; border: 1px solid #e2e8f0;")
                lw = QHBoxLayout(w)
                lw.setContentsMargins(12, 8, 12, 8)
                lw.setSpacing(12)
                # Imagen
                lbl_img = QLabel("📦")
                lbl_img.setStyleSheet("font-size: 16px; border: none; background: transparent;")
                lw.addWidget(lbl_img)
                # Info
                li = QVBoxLayout()
                li.setSpacing(0)
                l_desc = QLabel(p['descripcion'])
                l_desc.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: bold; font-size: 12px; border: none; background: transparent;")
                l_cod = QLabel(f"Cód: {p['codigo']}")
                l_cod.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px; border: none; background: transparent;")
                li.addWidget(l_desc)
                li.addWidget(l_cod)
                lw.addLayout(li)
                lw.addStretch()
                # Cantidad
                l_cant = QLabel(f"{p.get('vendido', 0):g} vendidos")
                l_cant.setStyleSheet(f"color: {COLOR_PRIMARY}; font-weight: bold; font-size: 12px; border: none; background: transparent;")
                lw.addWidget(l_cant)
                
                self.ly_items_frecuentes.addWidget(w)
        else:
            lbl_vacio = QLabel("No hay suficientes datos.")
            lbl_vacio.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-style: italic; border: none;")
            self.ly_items_frecuentes.addWidget(lbl_vacio)
            
        # Llenar Alertas Críticas
        while self.ly_items_alertas.count():
            item = self.ly_items_alertas.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        criticos = [p for p in self.datos_catalogo if p.get('activo', 1) == 1 and p['atp'] <= (p['stock_minimo'] if p['stock_minimo'] > 0 else 0)]
        # Ordenar por atp
        criticos.sort(key=lambda x: x['atp'])
        
        if criticos:
            for p in criticos[:3]:
                w = QFrame()
                w.setStyleSheet("background-color: #fff1f2; border-radius: 6px; border: 1px solid #fecdd3;")
                lw = QHBoxLayout(w)
                lw.setContentsMargins(12, 8, 12, 8)
                lw.setSpacing(12)
                # Info
                li = QVBoxLayout()
                li.setSpacing(0)
                l_desc = QLabel(p['descripcion'])
                l_desc.setStyleSheet("color: #9f1239; font-weight: bold; font-size: 12px; border: none; background: transparent;")
                l_cod = QLabel(f"Cód: {p['codigo']}")
                l_cod.setStyleSheet("color: #be123c; font-size: 11px; border: none; background: transparent;")
                li.addWidget(l_desc)
                li.addWidget(l_cod)
                lw.addLayout(li)
                lw.addStretch()
                # Cantidad
                l_cant = QLabel(f"Disp: {p['atp']:g}")
                l_cant.setStyleSheet("color: #e11d48; font-weight: 900; font-size: 12px; border: none; background: transparent;")
                lw.addWidget(l_cant)
                
                self.ly_items_alertas.addWidget(w)
        else:
            lbl_vacio = QLabel("No hay productos críticos.")
            lbl_vacio.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-style: italic; border: none;")
            self.ly_items_alertas.addWidget(lbl_vacio)
            
        self.aplicar_filtros()

    def aplicar_filtros(self):
        texto = self.input_buscar.text().strip().lower()
        idx_estado = self.combo_estado.currentIndex()
        unidad_filtro = self.combo_unidad.currentData()
        idx_orden = self.combo_orden.currentIndex()
        
        datos_filtrados = []
        for p in self.datos_catalogo:
            if texto and texto not in p["descripcion"].lower() and texto not in p["codigo"].lower():
                continue
                
            if unidad_filtro and p["unidad_base"] != unidad_filtro:
                continue
                
            activo = p.get("activo", 1)
            
            # Filtro Inactivos (índice 4)
            if idx_estado == 4:
                if activo == 1: continue
            else:
                # Cualquier otro estado solo muestra activos
                if activo == 0: continue
                
                atp = p["atp"]
                stk_min = p["stock_minimo"]
                
                estado_cat = 0 # Disponible
                if atp <= 0:
                    estado_cat = 2 # Sin Stock
                elif stk_min > 0 and atp <= stk_min:
                    estado_cat = 1 # Stock Bajo
                    
                if idx_estado == 1 and estado_cat != 0: continue
                if idx_estado == 2 and estado_cat != 1: continue
                if idx_estado == 3 and estado_cat != 2: continue
            
            datos_filtrados.append(p)
            
        if idx_orden == 1:
            datos_filtrados.sort(key=lambda x: x["atp"], reverse=True)
        elif idx_orden == 2:
            datos_filtrados.sort(key=lambda x: x["atp"])
        else:
            datos_filtrados.sort(key=lambda x: x["descripcion"].lower())
            
        self.renderizar_tabla(datos_filtrados)

    def renderizar_tabla(self, datos):

        self.tabla.setUpdatesEnabled(False)
        self.tabla.setRowCount(0)
        settings = QSettings("ConstrusecoPereyra", "StockConfig")
        mostrar_precio = settings.value("col_precio_visible", True, type=bool)
        mostrar_minimo = settings.value("col_minimo_visible", True, type=bool)
        mostrar_desglose = settings.value("col_desglose_visible", True, type=bool)
        
        self.tabla.setColumnHidden(8, not mostrar_precio)
        self.tabla.setColumnHidden(7, not mostrar_minimo)
        self.tabla.setColumnHidden(4, not mostrar_desglose)
        self.tabla.setColumnHidden(5, not mostrar_desglose)
        
        # Helper para alinear centrado
        def item_centrado(texto):
            it = QTableWidgetItem(str(texto))
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            return it
            
        def item_derecha(texto):
            it = QTableWidgetItem(str(texto))
            it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return it

        for i, p in enumerate(datos):
            self.tabla.insertRow(i)
            
            atp = p["atp"]
            fisico = p["stock_fisico"]
            comp = p["comprometido"]
            unidad = p["unidad_base"]
            stk_min = p["stock_minimo"]
            precio = p["precio_venta"]
            
            item_prod = QTableWidgetItem(p["descripcion"])
            item_cod = item_centrado(p["codigo"])
            
            # Unidad
            etiqueta_uni = unidad
            for val_bd, eq in UNIDADES_PERMITIDAS:
                if val_bd == unidad:
                    etiqueta_uni = eq
                    break
            item_uni = item_centrado(etiqueta_uni)
            
            item_fis = item_derecha(f"{fisico:g}")
            item_comp = item_derecha(f"{comp:g}")
            item_disp = item_derecha(f"{atp:g}")
            
            item_disp.setFont(QFont("Segoe UI", -1, QFont.Weight.Bold))
            
            item_min = item_derecha(f"{stk_min:g}")
            item_precio = item_derecha(f"$ {precio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            activo = p.get("activo", 1)
            
            str_estado = "Disponible"
            color_estado = COLOR_SUCCESS
            bg_disp = None
            
            if activo == 0:
                str_estado = "Inactivo"
                color_estado = "#64748b" # Gris
                bg_disp = QColor("#f1f5f9")
            elif atp <= 0:
                str_estado = "Sin Stock"
                color_estado = COLOR_DANGER
                bg_disp = QColor("#fee2e2")
            elif stk_min > 0 and atp <= stk_min:
                str_estado = "Stock Bajo"
                color_estado = COLOR_WARNING
                bg_disp = QColor("#fef3c7")
                
            item_est = item_centrado(str_estado)
            item_est.setForeground(QColor(color_estado))
            item_est.setFont(QFont("Segoe UI", -1, QFont.Weight.Bold))
            
            if bg_disp:
                item_disp.setForeground(QColor(color_estado))
                
            # Miniatura (columna 1)
            lbl_img = QLabel()
            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_img.setFixedSize(44, 44)
            img_path_raw = p.get("imagen_path")
            pix = None
            if img_path_raw:
                from ui.components.image_selector import resolver_ruta_imagen
                img_path = resolver_ruta_imagen(img_path_raw)
                if img_path:
                    pix = QPixmap(str(img_path))
                    if pix.isNull():
                        pix = None
            if pix:
                lbl_img.setPixmap(pix.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                lbl_img.setText("📦")
                lbl_img.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 18px;")
            
            self.tabla.setItem(i, 0, item_cod)
            self.tabla.setCellWidget(i, 1, lbl_img)
            self.tabla.setItem(i, 2, item_prod)
            self.tabla.setItem(i, 3, item_uni)
            self.tabla.setItem(i, 4, item_fis)
            self.tabla.setItem(i, 5, item_comp)
            self.tabla.setItem(i, 6, item_disp)
            self.tabla.setItem(i, 7, item_min)
            self.tabla.setItem(i, 8, item_precio)
            self.tabla.setItem(i, 9, item_est)
            
            # Botones de Acciones Rápidas
            w_acc = QWidget()
            l_acc = QHBoxLayout(w_acc)
            l_acc.setContentsMargins(0, 0, 0, 0)
            l_acc.setSpacing(0)
            
            btn_style_icon = f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_BG};
                }}
            """
            
            if activo == 0:
                btn_reactivar = QPushButton("♻️")
                btn_reactivar.setToolTip("Reactivar Producto")
                btn_reactivar.setFixedSize(28, 28)
                btn_reactivar.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_reactivar.setStyleSheet(btn_style_icon)
                btn_reactivar.clicked.connect(lambda checked, prod=p: self.reactivar_producto(prod))
                l_acc.addWidget(btn_reactivar, 0, Qt.AlignmentFlag.AlignCenter)
            else:
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
                        padding-bottom: 4px;
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
                        padding: 8px 24px 8px 12px;
                        border-radius: 4px;
                        color: {COLOR_TEXT_MAIN};
                        font-size: 13px;
                        margin: 2px;
                    }}
                    QMenu::item:selected {{
                        background-color: #f1f5f9;
                        color: {COLOR_PRIMARY};
                        font-weight: bold;
                    }}
                    QMenu::separator {{
                        height: 1px;
                        background: {COLOR_BORDER};
                        margin: 4px;
                    }}
                """)
                
                act_ver = QAction("👁 Ver detalle", self)
                act_ver.triggered.connect(lambda checked, prod=p: self.abrir_vista_detalle(prod))
                
                act_edit = QAction("✏️ Editar producto", self)
                act_edit.triggered.connect(lambda checked, prod=p: self.abrir_editar(prod))
                
                act_mod_precio = QAction("💲 Modificar precio", self)
                act_mod_precio.triggered.connect(lambda checked, prod=p: self.abrir_modificar_precio(prod))
                
                act_entrada = QAction("📥 Entrada de stock", self)
                act_entrada.triggered.connect(lambda checked, prod=p: self.abrir_modificar_stock(prod, modo='ENTRADA'))
                
                act_ajuste = QAction("📦 Ajuste de stock", self)
                act_ajuste.triggered.connect(lambda checked, prod=p: self.abrir_modificar_stock(prod, modo='AJUSTE'))
                
                act_eliminar = QAction("🗑️ Desactivar / Eliminar", self)
                act_eliminar.triggered.connect(lambda checked, prod=p: self.eliminar_desactivar_producto(prod))
                
                menu.addAction(act_ver)
                menu.addAction(act_edit)
                menu.addAction(act_mod_precio)
                menu.addSeparator()
                menu.addAction(act_entrada)
                menu.addAction(act_ajuste)
                menu.addSeparator()
                menu.addAction(act_eliminar)
                
                btn_more.setMenu(menu)
                
                l_acc.addWidget(btn_more, 0, Qt.AlignmentFlag.AlignCenter)
                
            self.tabla.setCellWidget(i, 10, w_acc)
            
            self.tabla.setRowHeight(i, 56)

        self.tabla.setUpdatesEnabled(True)
        self._actualizar_colores_seleccion()

    def reactivar_producto(self, prod):
        try:
            from db.queries_stock import reactivar_producto
            reactivar_producto(self.conn, prod['codigo'])
            QMessageBox.information(self, "Reactivado", f"El producto '{prod['descripcion']}' ({prod['codigo']}) ha sido reactivado.")
            self._notificar_cambios_globales()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al reactivar producto: {e}")

    def abrir_formulario_alta(self):
        dialogo = DialogoAgregarProducto(self.conn, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()

    def abrir_editar(self, producto_data):
        dialogo = DialogoEditarProducto(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()
            
    def abrir_modificar_precio(self, producto_data):
        from ui.modules.stock.dialogs_stock import DialogoModificarPrecio
        dialogo = DialogoModificarPrecio(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()

    def abrir_modificar_stock(self, producto_data, modo='ENTRADA'):
        dialogo = DialogoModificarStock(self.conn, producto_data, modo, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()

    def abrir_stock_min(self, producto_data):
        dialogo = DialogoStockMinimo(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()

    def abrir_importar_excel(self):
        dialogo = DialogoImportarExcel(self.conn, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()

    
    def abrir_frecuentes(self):
        from ui.modules.stock.dialogs_stock import DialogoProductosFrecuentes
        dialogo = DialogoProductosFrecuentes(self.conn, self.resaltar_producto_por_codigo, self)
        dialogo.exec()

    def abrir_configuracion_general(self):
        if DialogoConfiguracionGeneral(self).exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()
            

            
    def limpiar_resaltado(self):
        """Limpia la selección actual de la tabla."""
        self.tabla.clearSelection()
        self.tabla.setCurrentItem(None)

    def resaltar_producto_por_codigo(self, codigo):
        codigo = str(codigo).strip()
        
        # Limpiar filtros si es necesario para asegurar visibilidad
        # Esto automáticamente dispara aplicar_filtros() por las señales
        if self.combo_estado.currentIndex() != 0:
            self.combo_estado.setCurrentIndex(0)
        if self.input_buscar.text() != "":
            self.input_buscar.setText("")
            
        # Hacer scroll hasta la fila y SELECCIONAR NATIVAMENTE
        for row in range(self.tabla.rowCount()):
            item_cod = self.tabla.item(row, 0)
            if item_cod and item_cod.text() == codigo:
                self.tabla.selectRow(row)
                self.tabla.scrollToItem(item_cod, QAbstractItemView.ScrollHint.PositionAtCenter)
                break
                
    def _actualizar_colores_seleccion(self):
        sel_rows = {item.row() for item in self.tabla.selectedItems()}
        for r in range(self.tabla.rowCount()):
            is_sel = r in sel_rows
            
            # Columna Imagen (1)
            w_img = self.tabla.cellWidget(r, 1)
            if w_img and hasattr(w_img, "setStyleSheet"):
                color_img = "white" if is_sel else COLOR_TEXT_SEC
                w_img.setStyleSheet(f"color: {color_img}; font-size: 18px;")
            
            # Columna Acciones (10)
            w_acc = self.tabla.cellWidget(r, 10)
            if w_acc:
                from PyQt6.QtWidgets import QPushButton
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
                        }}
                        QPushButton::menu-indicator {{ image: none; width: 0px; }}
                    """)

    def on_tabla_double_click(self, row, col):
        if col == 10:  # Columna de acciones
            return
        item_cod = self.tabla.item(row, 0)
        if item_cod:
            codigo = item_cod.text()
            for p in self.datos_catalogo:
                if p['codigo'] == codigo:
                    self.abrir_vista_detalle(p)
                    break
                    
    def abrir_vista_detalle(self, producto):
        vista = VistaDetalleProducto(producto, self)
        vista.show()

    def abrir_alertas_inventario(self, event):
        # Dialogo popup para productos con bajo stock o sin stock
        from ui.modules.stock.dialogs_stock import DialogoAlertasInventario
        dlg = DialogoAlertasInventario(self.datos_catalogo, self.resaltar_producto_por_codigo, self)
        dlg.exec()
            
    def abrir_historial_movimientos(self):
        DialogoHistorialMovimientos(self.conn, self).exec()
        
    def ejecutar_limpieza_presupuestos(self):
        from db.conexion import limpiar_presupuestos_vencidos
        liberados = limpiar_presupuestos_vencidos(self.conn)
        if liberados > 0:
            QMessageBox.information(self, "Limpieza completada", f"Se vencieron y cerraron {liberados} presupuestos. El stock reservado volvió a estar disponible.")
            self._notificar_cambios_globales()
        elif liberados == 0:
            QMessageBox.information(self, "Limpieza", "No hay presupuestos vencidos que liberar.")
        else:
            QMessageBox.critical(self, "Error", "Ocurrió un error al limpiar los presupuestos.")

    def abrir_visualizacion_inventario(self):
        if DialogoVisualizacionInventario(self).exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()




    def eliminar_desactivar_producto(self, prod):
        from ui.modules.stock.dialogs_stock import DialogoDesactivarEliminar
        dialogo = DialogoDesactivarEliminar(self.conn, prod, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()
