import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QCursor, QPainter, QColor, QPen, QPainterPath
from datetime import datetime
from ui.core.theme import (COLOR_PRIMARY, COLOR_CARD_BG, COLOR_BORDER, 
                           COLOR_TEXT_MAIN, COLOR_TEXT_SEC, COLOR_SUCCESS, 
                           COLOR_WARNING, COLOR_DANGER)
from db.queries import obtener_productos_frecuentes, obtener_metricas_globales
from db.queries_presupuestos import obtener_kpis_presupuestos
from ui.components.operacion_base import formato_arg

def fecha_formateada():
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    hoy = datetime.now()
    return f"{dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month - 1]} de {hoy.year}"

TIPS = [
    "💡 Tip: Usá F2 para buscar productos rápidamente.",
    "💡 Tip: Usá F3 para buscar y asignar un cliente.",
    "💡 Tip: F11 vacía el carrito actual al instante.",
    "💡 Tip: Usá F12 para confirmar la operación actual."
]

class GraficoAnilloStock(QWidget):
    def __init__(self):
        super().__init__()
        self.total = 0
        self.bajo = 0
        self.sin = 0
        self.setMinimumSize(160, 160)
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def actualizar_datos(self, metricas):
        self.total = metricas.get('total_productos', 0)
        self.bajo = metricas.get('bajo_stock', 0)
        self.sin = metricas.get('sin_stock', 0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.total == 0:
            painter.setPen(QColor(COLOR_TEXT_SEC))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin productos")
            return
            
        ok_stock = max(0, self.total - self.bajo - self.sin)
        
        # Calcular rectangulo para el anillo
        size = min(self.width(), self.height()) - 40
        rect = QRectF((self.width() - size) / 2, (self.height() - size) / 2, size, size)
        
        # Grosor del anillo
        pen_width = 20
        
        # Trazar sectores
        angulo_inicio = 90 * 16 # Empezar desde arriba
        
        valores = [
            (ok_stock, COLOR_SUCCESS),
            (self.bajo, COLOR_WARNING),
            (self.sin, COLOR_DANGER)
        ]
        
        for valor, color_hex in valores:
            if valor <= 0:
                continue
            angulo_span = int(- (valor / self.total) * 360 * 16)
            pen = QPen(QColor(color_hex))
            pen.setWidth(pen_width)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            painter.drawArc(rect, angulo_inicio, angulo_span)
            angulo_inicio += angulo_span
            
        # Dibujar texto central
        painter.setPen(QColor(COLOR_TEXT_MAIN))
        font_total = self.font()
        font_total.setPointSize(24)
        font_total.setBold(True)
        painter.setFont(font_total)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self.total))
        
        font_lbl = self.font()
        font_lbl.setPointSize(10)
        painter.setFont(font_lbl)
        painter.setPen(QColor(COLOR_TEXT_SEC))
        
        # Bajar un poco el texto secundario
        rect_sub = self.rect()
        rect_sub.translate(0, 30)
        painter.drawText(rect_sub, Qt.AlignmentFlag.AlignCenter, "Productos")


class GraficoMasVendidos(QWidget):
    def __init__(self):
        super().__init__()
        self.productos = []
        self.setMinimumHeight(200)

    def actualizar_datos(self, productos):
        self.productos = productos
        self.update()

    def paintEvent(self, event):
        if not self.productos:
            painter = QPainter(self)
            painter.setPen(QColor(COLOR_TEXT_SEC))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin datos de ventas recientes")
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        max_vendido = max((p.get('vendido', 0) for p in self.productos), default=1)
        if max_vendido == 0: max_vendido = 1
        
        margen_izq = 10
        margen_der = 60
        espacio_y = self.height() / len(self.productos)
        alto_barra = min(24, int(espacio_y * 0.4))
        
        font_texto = self.font()
        font_texto.setPointSize(10)
        painter.setFont(font_texto)
        
        for i, p in enumerate(self.productos):
            y_centro = i * espacio_y + espacio_y / 2
            
            # Texto descriptivo (arriba de la barra)
            desc = p.get('descripcion', '')
            vendido = p.get('vendido', 0)
            unidad = p.get('unidad_base', 'u')
            
            painter.setPen(QColor(COLOR_TEXT_MAIN))
            painter.drawText(margen_izq, int(y_centro - alto_barra/2 - 4), f"{desc}")
            
            # Fondo barra
            rect_fondo = QRectF(margen_izq, y_centro - alto_barra/2 + 2, self.width() - margen_izq - margen_der, alto_barra)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(COLOR_BORDER))
            painter.drawRoundedRect(rect_fondo, alto_barra/2, alto_barra/2)
            
            # Barra progreso
            ancho_barra = (vendido / max_vendido) * rect_fondo.width()
            if ancho_barra > 0:
                rect_progreso = QRectF(margen_izq, y_centro - alto_barra/2 + 2, ancho_barra, alto_barra)
                painter.setBrush(QColor(COLOR_PRIMARY))
                painter.drawRoundedRect(rect_progreso, alto_barra/2, alto_barra/2)
                
            # Etiqueta valor
            painter.setPen(QColor(COLOR_TEXT_SEC))
            painter.drawText(int(margen_izq + rect_fondo.width() + 10), int(y_centro + alto_barra/2 + 4), f"{vendido} {unidad}")

class TarjetaAtajo(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, icono, titulo, descripcion):
        super().__init__()
        self.setObjectName("tarjeta_clickable")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        lbl_icono = QLabel(icono)
        lbl_icono.setStyleSheet("font-size: 32px;")
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 16px; font-weight: 800;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_desc = QLabel(descripcion)
        lbl_desc.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px;")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setWordWrap(True)
        
        layout.addWidget(lbl_icono)
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_desc)
        
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.clicked.emit()

class PestanaInicio(QWidget):
    nueva_venta_solicitada = pyqtSignal()
    nuevo_presupuesto_solicitado = pyqtSignal()
    ver_stock_solicitado = pyqtSignal()
    ver_clientes_solicitado = pyqtSignal()
    ver_presupuestos_solicitado = pyqtSignal()
    
    def __init__(self, conexion_db):
        super().__init__()
        self.conn = conexion_db
        self.init_ui()
        
    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Encabezado
        ly_encabezado = QHBoxLayout()
        ly_encabezado.setContentsMargins(0, 0, 0, 0)
        
        ly_textos = QVBoxLayout()
        lbl_saludo = QLabel("👋 ¡Bienvenido!")
        lbl_saludo.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 24px; font-weight: bold;")
        lbl_fecha = QLabel(fecha_formateada())
        lbl_fecha.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 14px;")
        ly_textos.addWidget(lbl_saludo)
        ly_textos.addWidget(lbl_fecha)
        
        btn_ayuda = QPushButton("ⓘ Ayuda")
        btn_ayuda.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ayuda.setStyleSheet(f"background-color: transparent; color: {COLOR_TEXT_SEC}; font-size: 13px; font-weight: 600; padding: 6px 12px; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        btn_ayuda.clicked.connect(self._mostrar_ayuda)
        
        ly_encabezado.addLayout(ly_textos)
        ly_encabezado.addStretch()
        ly_encabezado.addWidget(btn_ayuda, alignment=Qt.AlignmentFlag.AlignTop)
        
        layout.addLayout(ly_encabezado)
        layout.addSpacing(10)
        
        # Atajos
        layout_atajos = QHBoxLayout()
        layout_atajos.setSpacing(15)
        
        atajo_venta = TarjetaAtajo("🛒", "Nueva Venta", "Iniciar una venta rápida")
        atajo_venta.clicked.connect(self.nueva_venta_solicitada.emit)
        
        atajo_presupuesto = TarjetaAtajo("📄", "Nuevo Presupuesto", "Crear presupuesto")
        atajo_presupuesto.clicked.connect(self.nuevo_presupuesto_solicitado.emit)
        
        atajo_stock = TarjetaAtajo("📦", "Ver Stock", "Consultar stock")
        atajo_stock.clicked.connect(self.ver_stock_solicitado.emit)
        
        atajo_clientes = TarjetaAtajo("👥", "Ver Clientes", "Gestionar clientes")
        atajo_clientes.clicked.connect(self.ver_clientes_solicitado.emit)
        
        layout_atajos.addWidget(atajo_venta)
        layout_atajos.addWidget(atajo_presupuesto)
        layout_atajos.addWidget(atajo_stock)
        layout_atajos.addWidget(atajo_clientes)
        
        layout.addLayout(layout_atajos)
        layout.addSpacing(10)
        
        # KPIs Stock
        lbl_titulo_kpi = QLabel("📊 Estado del Stock")
        lbl_titulo_kpi.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl_titulo_kpi)
        
        self.ly_kpis = QHBoxLayout()
        self.ly_kpis.setSpacing(15)
        
        self.kpi_total_val, frame_t = self._crear_kpi_card("Total Productos")
        self.kpi_valor_val, frame_v = self._crear_kpi_card("Valor Stock")
        self.kpi_bajo_val, frame_b = self._crear_kpi_card("Stock Bajo")
        self.kpi_sin_val, frame_s = self._crear_kpi_card("Sin Stock")
        
        self.ly_kpis.addWidget(frame_t)
        self.ly_kpis.addWidget(frame_v)
        self.ly_kpis.addWidget(frame_b)
        self.ly_kpis.addWidget(frame_s)
        layout.addLayout(self.ly_kpis)
        layout.addSpacing(10)
        
        # Fila: Presupuestos y Tips
        ly_alertas = QHBoxLayout()
        ly_alertas.setSpacing(15)
        
        # Widget Presupuestos
        self.frame_presup = QFrame()
        self.frame_presup.setObjectName("tarjeta_clickable")
        self.frame_presup.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.frame_presup.mousePressEvent = lambda e: self.ver_presupuestos_solicitado.emit()
        
        ly_p = QHBoxLayout(self.frame_presup)
        ly_p.setContentsMargins(20, 15, 20, 15)
        
        ly_p_info = QVBoxLayout()
        lbl_tit_p = QLabel("Presupuestos")
        lbl_tit_p.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: bold; font-size: 16px;")
        self.lbl_presup_activos = QLabel("0 activos")
        self.lbl_presup_activos.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 14px;")
        ly_p_info.addWidget(lbl_tit_p)
        ly_p_info.addWidget(self.lbl_presup_activos)
        
        self.lbl_presup_vencidos = QLabel()
        self.lbl_presup_vencidos.setVisible(False)
        self.lbl_presup_vencidos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ly_p.addLayout(ly_p_info)
        ly_p.addStretch()
        ly_p.addWidget(self.lbl_presup_vencidos, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        ly_alertas.addWidget(self.frame_presup, stretch=5)
        
        # Widget Tip
        self.frame_tip = QFrame()
        self.frame_tip.setObjectName("tarjeta_blanca")
        ly_t = QHBoxLayout(self.frame_tip)
        ly_t.setContentsMargins(15, 10, 15, 10)
        self.lbl_tip = QLabel()
        self.lbl_tip.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 13px; font-style: italic;")
        self.lbl_tip.setWordWrap(True)
        self.lbl_tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ly_t.addWidget(self.lbl_tip, alignment=Qt.AlignmentFlag.AlignCenter)
        ly_alertas.addWidget(self.frame_tip, stretch=2)
        
        layout.addLayout(ly_alertas)
        layout.addSpacing(10)
        
        # Layout Gráficos
        ly_graficos = QHBoxLayout()
        ly_graficos.setSpacing(15)
        
        # Gráfico Stock
        self.frame_stock = QFrame()
        self.frame_stock.setObjectName("tarjeta_blanca")
        ly_stock = QVBoxLayout(self.frame_stock)
        lbl_tit_stock = QLabel("Estado del Stock")
        lbl_tit_stock.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: bold; font-size: 16px;")
        self.grafico_stock = GraficoAnilloStock()
        
        ly_leyenda = QHBoxLayout()
        for texto, color in [("OK", COLOR_SUCCESS), ("Bajo", COLOR_WARNING), ("Sin Stock", COLOR_DANGER)]:
            lbl_color = QLabel("■")
            lbl_color.setStyleSheet(f"color: {color}; font-size: 14px;")
            lbl_txt = QLabel(texto)
            lbl_txt.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px;")
            ly_leyenda.addWidget(lbl_color)
            ly_leyenda.addWidget(lbl_txt)
        ly_leyenda.addStretch()
        
        ly_stock.addWidget(lbl_tit_stock)
        ly_stock.addWidget(self.grafico_stock)
        ly_stock.addLayout(ly_leyenda)
        ly_graficos.addWidget(self.frame_stock, stretch=1)
        
        # Gráfico Ventas
        self.frame_ventas = QFrame()
        self.frame_ventas.setObjectName("tarjeta_blanca")
        ly_ventas = QVBoxLayout(self.frame_ventas)
        lbl_tit_ventas = QLabel("Más vendidos · últimos 30 días")
        lbl_tit_ventas.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: bold; font-size: 16px;")
        self.grafico_ventas = GraficoMasVendidos()
        ly_ventas.addWidget(lbl_tit_ventas)
        ly_ventas.addWidget(self.grafico_ventas)
        ly_graficos.addWidget(self.frame_ventas, stretch=2)
        
        layout.addLayout(ly_graficos)
        
        layout.addStretch()
        
        scroll.setWidget(main_widget)
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0,0,0,0)
        main_lay.addWidget(scroll)
        
        self.setStyleSheet(f"""
            QFrame#tarjeta_blanca, QFrame#tarjeta_clickable {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
            }}
            QFrame#tarjeta_clickable:hover {{
                border: 1px solid {COLOR_PRIMARY};
            }}
        """)

    def _crear_kpi_card(self, titulo):
        f = QFrame()
        f.setObjectName("tarjeta_blanca")
        ly = QVBoxLayout(f)
        ly.setContentsMargins(24, 24, 24, 24)
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 13px; font-weight: bold;")
        lbl_v = QLabel("0")
        lbl_v.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 24px; font-weight: bold;")
        ly.addWidget(lbl_t)
        ly.addWidget(lbl_v)
        return lbl_v, f
        
    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_datos()
        
    def cargar_datos(self):
        try:
            # Tip
            self.lbl_tip.setText(random.choice(TIPS))
            
            # KPIs Stock
            metricas = obtener_metricas_globales(self.conn)
            self.kpi_total_val.setText(f"{metricas['total_productos']:,}".replace(",", "."))
            self.kpi_valor_val.setText(f"$ {formato_arg(metricas['valor_inventario'])}")
            
            BADGE_WARNING_STYLE = f"background-color: {COLOR_WARNING}; color: {COLOR_CARD_BG}; padding: 4px 10px; border-radius: 6px; font-size: 16px; font-weight: bold;"
            BADGE_DANGER_STYLE = f"background-color: {COLOR_DANGER}; color: {COLOR_CARD_BG}; padding: 4px 10px; border-radius: 6px; font-size: 16px; font-weight: bold;"
            DEFAULT_KPI_STYLE = f"color: {COLOR_TEXT_MAIN}; font-size: 24px; font-weight: bold; background-color: transparent; padding: 0px;"

            b = metricas['bajo_stock']
            self.kpi_bajo_val.setText(str(b))
            if b > 0:
                self.kpi_bajo_val.setStyleSheet(BADGE_WARNING_STYLE)
            else:
                self.kpi_bajo_val.setStyleSheet(DEFAULT_KPI_STYLE)
            
            s = metricas['sin_stock']
            self.kpi_sin_val.setText(str(s))
            if s > 0:
                self.kpi_sin_val.setStyleSheet(BADGE_DANGER_STYLE)
            else:
                self.kpi_sin_val.setStyleSheet(DEFAULT_KPI_STYLE)
                
            # KPIs Presupuestos
            presup = obtener_kpis_presupuestos(self.conn)
            self.lbl_presup_activos.setText(f"{presup['activos']} activos")
            v = presup['vencidos']
            if v > 0:
                self.lbl_presup_vencidos.setText(f"{v} presupuesto{'s' if v != 1 else ''} vencido{'s' if v != 1 else ''}")
                self.lbl_presup_vencidos.setStyleSheet(f"background-color: {COLOR_DANGER}; color: {COLOR_CARD_BG}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;")
                self.lbl_presup_vencidos.setVisible(True)
            else:
                self.lbl_presup_vencidos.setVisible(False)
                
            # Actualizar Gráficos
            self.grafico_stock.actualizar_datos(metricas)
            productos_frecuentes = obtener_productos_frecuentes(self.conn)
            self.grafico_ventas.actualizar_datos(productos_frecuentes)
        except Exception as e:
            print(f"[INICIO] Error al cargar datos del panel: {e}")

    def _mostrar_ayuda(self):
        from ui.components.ayuda import DialogoAyudaContextual
        texto = (
            "<p><b>OBJETIVO:</b></p>"
            "<p>Proporcionar una vista general y rápida (Dashboard) del estado del negocio, permitiendo el acceso inmediato a las operaciones más comunes y resumiendo la información clave.</p>"
            "<br>"
            "<p><b>QUÉ PUEDE HACER EL USUARIO:</b></p>"
            "<ul>"
            "<li>Visualizar atajos rápidos para crear ventas, presupuestos, consultar clientes o stock.</li>"
            "<li>Consultar indicadores rápidos (KPI) sobre el inventario valorizado y los presupuestos vigentes.</li>"
            "<li>Recibir alertas tempranas sobre productos con stock bajo o nulo.</li>"
            "<li>Observar el rendimiento de los productos más vendidos en los últimos 30 días.</li>"
            "</ul>"
            "<br>"
            "<p><b>SECCIONES DE LA PANTALLA:</b></p>"
            "<ul>"
            "<li><b>Atajos Principales:</b> Botones de acceso rápido a las tareas cotidianas.</li>"
            "<li><b>Tarjetas KPI (Stock y Presupuestos):</b> Resúmenes numéricos globales (valor total del inventario, productos sin stock, presupuestos activos/vencidos).</li>"
            "<li><b>Gráfico de Inventario:</b> Distribución visual del stock por estado (Disponible, Bajo, Sin Stock).</li>"
            "<li><b>Ranking de Ventas:</b> Gráfico de barras horizontales mostrando los productos más solicitados en el mes.</li>"
            "</ul>"
            "<br>"
            "<p><b>EXPLICACIÓN DE BOTONES:</b></p>"
            "<ul>"
            "<li><b>Nueva Venta:</b> Inicia el comprobante de venta.</li>"
            "<li><b>Nuevo Presupuesto:</b> Inicia la carga de un presupuesto temporal.</li>"
            "<li><b>Ver Stock:</b> Abre el inventario completo.</li>"
            "<li><b>Ver Clientes:</b> Abre el catálogo de clientes registrados.</li>"
            "</ul>"
            "<br>"
            "<p><b>FLUJO DE TRABAJO RECOMENDADO:</b></p>"
            "<ol>"
            "<li>Al iniciar la jornada, revisar las alertas rojas (productos Sin Stock y Presupuestos Vencidos).</li>"
            "<li>Utilizar los atajos superiores para saltar rápidamente a la operación requerida sin usar el menú lateral.</li>"
            "</ol>"
            "<br>"
            "<p><b>CONSEJOS DE USO Y BUENAS PRÁCTICAS:</b></p>"
            "<ul>"
            "<li>Mantené el stock al día y configurá correctamente los mínimos para que los indicadores de esta pantalla sean precisos y útiles.</li>"
            "</ul>"
        )
        dialogo = DialogoAyudaContextual("Ayuda: Dashboard de Inicio", "Vista general del sistema y accesos rápidos", texto, self)
        dialogo.exec()
