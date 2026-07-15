import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QFrame, QDialog, QFormLayout, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QCursor, QAction, QBrush, QPixmap

from db.queries import obtener_stocks_todos, obtener_metricas_globales, obtener_productos_frecuentes, UNIDADES_PERMITIDAS
from db.queries_stock import migrar_esquema_stock
from ui.modules.stock.dialogs_stock import (
    DialogoAgregarProducto, DialogoEditarProducto,
    DialogoStockMinimo, DialogoEntradaStock, DialogoAjusteInventario,
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
                border-radius: 8px;
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
        layout.setSpacing(4)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 13px; font-weight: bold;")
        
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
                border-radius: 8px;
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
                padding: 10px 18px; 
                border-radius: 6px; 
                font-size: 13px;
                border: none;
            }}
            QPushButton.primario:hover {{ background-color: #1d4ed8; }}
            
            QPushButton.secundario {{
                background-color: {COLOR_CARD_BG}; 
                color: {COLOR_TEXT_MAIN}; 
                font-weight: bold;
                padding: 10px 18px; 
                border-radius: 6px; 
                font-size: 13px;
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
                padding: 6px;
                font-size: 13px;
            }}
            
            /* Tabla */
            QTableWidget {{
                background-color: {COLOR_CARD_BG};
                color: {COLOR_TEXT_MAIN};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                gridline-color: {COLOR_BG};
                font-size: 13px;
                selection-background-color: #eff6ff;
                selection-color: {COLOR_TEXT_MAIN};
            }}
            QHeaderView::section {{
                background-color: #f1f5f9;
                color: {COLOR_TEXT_SEC};
                font-weight: bold;
                padding: 10px;
                border: none;
                border-bottom: 2px solid {COLOR_BORDER};
                border-right: 1px solid {COLOR_BG};
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # 1. ENCABEZADO
        header_layout = QHBoxLayout()
        titles_layout = QVBoxLayout()
        titles_layout.setSpacing(4)
        
        lbl_titulo = QLabel("Control de Stock")
        lbl_titulo.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {COLOR_TEXT_MAIN};")
        lbl_subtitulo = QLabel("Gestión de inventario, disponibilidad y métricas operativas")
        lbl_subtitulo.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_SEC};")
        
        titles_layout.addWidget(lbl_titulo)
        titles_layout.addWidget(lbl_subtitulo)
        
        btn_actualizar = QPushButton("⟳")
        btn_actualizar.setToolTip("Actualizar")
        btn_actualizar.setFixedSize(32, 32)
        btn_actualizar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_actualizar.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-size: 18px;
                color: {COLOR_TEXT_MAIN};
            }}
            QPushButton:hover {{
                background-color: {COLOR_BG};
                border-color: {COLOR_PRIMARY};
                color: {COLOR_PRIMARY};
            }}
        """)
        btn_actualizar.clicked.connect(self.actualizar_vista)
        
        btn_importar = QPushButton("Importar / Exportar ▾")
        btn_importar.setProperty("class", "secundario")
        btn_importar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Menu Importar / Exportar
        menu_excel = QMenu(btn_importar)
        
        act_importar = QAction("📥 Importar desde Excel", self)
        act_importar.triggered.connect(self.abrir_importar_excel)
        
        act_exportar = QAction("📤 Exportar Inventario", self)
        act_exportar.triggered.connect(lambda: exportar_inventario_excel(self.conn, self))
        
        act_plantilla = QAction("📄 Descargar Plantilla", self)
        act_plantilla.triggered.connect(lambda: generar_plantilla_excel(self))
        
        menu_excel.addAction(act_importar)
        menu_excel.addAction(act_exportar)
        menu_excel.addSeparator()
        menu_excel.addAction(act_plantilla)
        
        btn_importar.setMenu(menu_excel)
        
        btn_ajustes = QPushButton("Ajustes de Stock ▾")
        btn_ajustes.setProperty("class", "secundario")
        btn_ajustes.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Menu Ajustes
        menu_ajustes = QMenu(btn_ajustes)
        
        act_conf = QAction("⚙️ Configuración general", self)
        act_conf.triggered.connect(self.abrir_configuracion_general)
        
        act_hist = QAction("📜 Historial de movimientos", self)
        act_hist.triggered.connect(self.abrir_historial_movimientos)
        
        act_lib = QAction("🧹 Liberar presupuestos vencidos", self)
        act_lib.triggered.connect(self.ejecutar_limpieza_presupuestos)
        
        act_vis = QAction("👁 Opciones de visualización", self)
        act_vis.triggered.connect(self.abrir_visualizacion_inventario)
        
        menu_ajustes.addAction(act_conf)
        menu_ajustes.addAction(act_hist)
        menu_ajustes.addSeparator()
        menu_ajustes.addAction(act_lib)
        menu_ajustes.addSeparator()
        menu_ajustes.addAction(act_vis)
        
        btn_ajustes.setMenu(menu_ajustes)
        
        btn_agregar = QPushButton("+ Nuevo Producto")
        btn_agregar.setProperty("class", "primario")
        btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_agregar.clicked.connect(self.abrir_formulario_alta)
        
        header_layout.addLayout(titles_layout)
        header_layout.addStretch()
        header_layout.addWidget(btn_actualizar)
        header_layout.addWidget(btn_importar)
        header_layout.addWidget(btn_ajustes)
        header_layout.addWidget(btn_agregar)
        
        main_layout.addLayout(header_layout)
        
        # 2. TARJETAS DE RESUMEN
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.tarjeta_total = TarjetaMetrica("TOTAL ACTIVOS", "0")
        self.tarjeta_valor = TarjetaMetrica("VALOR INVENTARIO", "$ 0,00", color_borde=COLOR_SUCCESS)
        self.tarjeta_bajo = TarjetaMetrica("STOCK BAJO", "0", color_borde=COLOR_WARNING)
        self.tarjeta_sin = TarjetaMetrica("SIN STOCK", "0", color_borde=COLOR_DANGER)
        
        self.tarjeta_total.clicked_tarjeta.connect(self.filtro_metrica_click)
        self.tarjeta_bajo.clicked_tarjeta.connect(self.filtro_metrica_click)
        self.tarjeta_sin.clicked_tarjeta.connect(self.filtro_metrica_click)
        
        cards_layout.addWidget(self.tarjeta_total)
        cards_layout.addWidget(self.tarjeta_valor)
        cards_layout.addWidget(self.tarjeta_bajo)
        cards_layout.addWidget(self.tarjeta_sin)
        
        main_layout.addLayout(cards_layout)
        
        # 3. FRECUENTES Y AVISOS
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(24)
        
        # Frecuentes
        frecuentes_container = QVBoxLayout()
        frecuentes_container.setSpacing(12)
        lbl_frecuentes = QLabel("Productos de Mayor Rotación (Últimos 30 días)")
        lbl_frecuentes.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {COLOR_TEXT_MAIN};")
        frecuentes_container.addWidget(lbl_frecuentes)
        
        self.layout_tarjetas_frec = QHBoxLayout()
        self.layout_tarjetas_frec.setSpacing(16)
        self.layout_tarjetas_frec.setAlignment(Qt.AlignmentFlag.AlignLeft)
        frecuentes_container.addLayout(self.layout_tarjetas_frec)
        frecuentes_container.addStretch()
        
        mid_layout.addLayout(frecuentes_container, stretch=3)
        
        # Aviso Stock Bajo
        aviso_container = QFrame()
        aviso_container.setStyleSheet(f"""
            QFrame {{
                background-color: #fffbeb;
                border: 1px solid #fde68a;
                border-radius: 8px;
            }}
        """)
        aviso_layout = QVBoxLayout(aviso_container)
        aviso_layout.setContentsMargins(20, 20, 20, 20)
        aviso_layout.setSpacing(8)
        
        lbl_aviso_tit = QLabel("⚠️ Alerta de Inventario")
        lbl_aviso_tit.setStyleSheet("color: #b45309; font-weight: 900; font-size: 14px; border: none;")
        self.lbl_aviso_desc = QLabel("Todo en orden. No hay productos con stock crítico.")
        self.lbl_aviso_desc.setStyleSheet("color: #92400e; font-size: 13px; border: none;")
        self.lbl_aviso_desc.setWordWrap(True)
        
        aviso_layout.addWidget(lbl_aviso_tit)
        aviso_layout.addWidget(self.lbl_aviso_desc)
        aviso_layout.addStretch()
        
        # Make interactive
        aviso_container.setCursor(Qt.CursorShape.PointingHandCursor)
        aviso_container.mousePressEvent = self.abrir_alertas_inventario
        
        mid_layout.addWidget(aviso_container, stretch=1)
        
        main_layout.addLayout(mid_layout)
        
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
            "Código", "Img", "Producto", "Unidad", "Stk. Físico", "Comprometido", 
            "Disponible", "Stk. Mínimo", "Precio", "Estado", "Acciones"
        ])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(48)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.setShowGrid(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(self.tabla.styleSheet() + """
            QTableWidget { alternate-background-color: #fafbfd; }
            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #0f172a;
            }
        """)
        self.tabla.cellDoubleClicked.connect(self.on_tabla_double_click)
        
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
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)   # Acciones
        self.tabla.setColumnWidth(1, 52)
        self.tabla.setColumnWidth(10, 110)
        
        main_layout.addWidget(self.tabla, stretch=1)
        
        # Conexiones de filtros
        self.input_buscar.textChanged.connect(self.aplicar_filtros)
        self.combo_estado.currentIndexChanged.connect(self.aplicar_filtros)
        self.combo_unidad.currentIndexChanged.connect(self.aplicar_filtros)
        self.combo_orden.currentIndexChanged.connect(self.aplicar_filtros)
        
        # Conexiones de métricas
        self.tarjeta_total.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tarjeta_bajo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tarjeta_sin.setCursor(Qt.CursorShape.PointingHandCursor)


    def actualizar_vista(self):
        """Coordina la recarga manual de toda la vista de stock, reutilizando la lógica principal."""
        self.cargar_datos()

    def cargar_datos(self):
        # 1. Cargar métricas globales
        metricas = obtener_metricas_globales(self.conn)
        self.tarjeta_total.set_valor(metricas["total_productos"])
        
        valor = metricas["valor_inventario"]
        self.tarjeta_valor.set_valor(f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        self.tarjeta_bajo.set_valor(metricas["bajo_stock"])
        self.tarjeta_sin.set_valor(metricas["sin_stock"])
        
        if metricas["bajo_stock"] > 0 or metricas["sin_stock"] > 0:
            msj = f"Atención: Tienes {metricas['bajo_stock']} productos con stock bajo y {metricas['sin_stock']} sin stock disponible."
            self.lbl_aviso_desc.setText(msj)
            self.lbl_aviso_desc.setStyleSheet("color: #991b1b; font-size: 13px; border: none;")
        else:
            self.lbl_aviso_desc.setText("Todo en orden. No hay productos con stock crítico.")
            self.lbl_aviso_desc.setStyleSheet("color: #92400e; font-size: 13px; border: none;")
            
        # 2. Cargar frecuentes
        while self.layout_tarjetas_frec.count():
            item = self.layout_tarjetas_frec.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        settings = QSettings("ConstrusecoPereyra", "StockConfig")
        limite = settings.value("freq_limit", 3, type=int)
        dias = settings.value("freq_days", 30, type=int)
        
        frecuentes = obtener_productos_frecuentes(self.conn, limite=limite, dias=dias)
        if frecuentes:
            for p in frecuentes:
                tarjeta = TarjetaFrecuente(p)
                tarjeta.clicked_codigo.connect(self.resaltar_producto_por_codigo)
                self.layout_tarjetas_frec.addWidget(tarjeta)
        else:
            lbl_vacio = QLabel(f"No hay suficientes datos de ventas recientes en los últimos {dias} días.")
            lbl_vacio.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-style: italic;")
            self.layout_tarjetas_frec.addWidget(lbl_vacio)
            
        # 3. Cargar catálogo completo
        self.datos_catalogo = obtener_stocks_todos(self.conn, incluir_inactivos=True)
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
        print(f"[TRACE] renderizar_tabla llamado con {len(datos)} elementos")
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
            
            item_fis = item_centrado(f"{fisico:g}")
            item_comp = item_centrado(f"{comp:g}")
            item_disp = item_centrado(f"{atp:g}")
            
            item_disp.setFont(QFont("Segoe UI", -1, QFont.Weight.Bold))
            
            item_min = item_centrado(f"{stk_min:g}")
            item_precio = item_centrado(f"$ {precio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
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
                item_disp.setBackground(bg_disp)
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
            
            # Boton Acciones con Menu
            btn_acc = QPushButton("⚩️ Acciones")
            btn_acc.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_acc.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLOR_TEXT_MAIN};
                    font-weight: bold;
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }}
                QPushButton:hover {{ background: {COLOR_BG}; border-color: {COLOR_PRIMARY}; color: {COLOR_PRIMARY}; }}
                QPushButton::menu-indicator {{ image: none; }}
            """)
            
            menu = QMenu(btn_acc)
            
            if activo == 0:
                act_ver = QAction("👁 Ver Detalles", self)
                act_ver.triggered.connect(lambda checked, prod=p: self.abrir_vista_detalle(prod))
                act_reactivar = QAction("♻️ Reactivar Producto", self)
                act_reactivar.triggered.connect(lambda checked, prod=p: self.reactivar_producto(prod))
                
                menu.addAction(act_ver)
                menu.addSeparator()
                menu.addAction(act_reactivar)
            else:
                act_ver = QAction("👁 Ver Detalles", self)
                act_ver.triggered.connect(lambda checked, prod=p: self.abrir_vista_detalle(prod))
                act_edit = QAction("✏️ Editar", self)
                act_edit.triggered.connect(lambda checked, prod=p: self.abrir_editar(prod))
                act_ent = QAction("📥 Entrada Stock", self)
                act_ent.triggered.connect(lambda checked, prod=p: self.abrir_entrada(prod))
                act_aju = QAction("⚖️ Ajuste Inventario", self)
                act_aju.triggered.connect(lambda checked, prod=p: self.abrir_ajuste(prod))
                act_min = QAction("⚠️ Configurar Mínimo", self)
                act_min.triggered.connect(lambda checked, prod=p: self.abrir_stock_min(prod))
                
                menu.addAction(act_ver)
                menu.addAction(act_edit)
                menu.addSeparator()
                menu.addAction(act_ent)
                menu.addAction(act_aju)
                menu.addSeparator()
                menu.addAction(act_min)
            
            btn_acc.setMenu(menu)
            
            w_acc = QWidget()
            l_acc = QHBoxLayout(w_acc)
            l_acc.setContentsMargins(4,4,4,4)
            l_acc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l_acc.addWidget(btn_acc)
            self.tabla.setCellWidget(i, 10, w_acc)
            

            self.tabla.setRowHeight(i, 46)

    def reactivar_producto(self, prod):
        try:
            from db.queries_stock import reactivar_producto
            reactivar_producto(self.conn, prod['codigo'])
            QMessageBox.information(self, "Reactivado", f"El producto {prod['codigo']} ha sido reactivado.")
            self.cargar_datos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al reactivar producto: {e}")

    def abrir_formulario_alta(self):
        dialogo = DialogoAgregarProducto(self.conn, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()

    def abrir_editar(self, producto_data):
        dialogo = DialogoEditarProducto(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()

    def abrir_entrada(self, producto_data):
        dialogo = DialogoEntradaStock(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()

    def abrir_ajuste(self, producto_data):
        dialogo = DialogoAjusteInventario(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()

    def abrir_stock_min(self, producto_data):
        dialogo = DialogoStockMinimo(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()

    def abrir_importar_excel(self):
        dialogo = DialogoImportarExcel(self.conn, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()

    def abrir_configuracion_general(self):
        if DialogoConfiguracionGeneral(self).exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()
            
    def filtro_metrica_click(self, tarjeta):
        if tarjeta == self.tarjeta_total:
            self.combo_estado.setCurrentIndex(0)
        elif tarjeta == self.tarjeta_bajo:
            self.combo_estado.setCurrentIndex(2)
        elif tarjeta == self.tarjeta_sin:
            self.combo_estado.setCurrentIndex(3)
            
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
            QMessageBox.information(self, "Limpieza completada", f"Se han liberado {liberados} presupuestos vencidos. El stock comprometido ha vuelto a estar disponible.")
            self.cargar_datos()
        elif liberados == 0:
            QMessageBox.information(self, "Limpieza", "No hay presupuestos vencidos que liberar.")
        else:
            QMessageBox.critical(self, "Error", "Ocurrió un error al limpiar los presupuestos.")

    def abrir_visualizacion_inventario(self):
        if DialogoVisualizacionInventario(self).exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()



