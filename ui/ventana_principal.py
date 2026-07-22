from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QFrame,
                             QGraphicsOpacityEffect, QMessageBox, QMenu, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QVariantAnimation, QPropertyAnimation, QEasingCurve, QSettings, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPainterPath
from pathlib import Path
from ui.modules.stock.tab_stock import PestanaStock
from ui.modules.ventas.tab_ventas import PestanaNuevaVenta
from ui.modules.clientes.tab_clientes import PestanaClientes
from ui.modules.presupuestos.tab_presupuestos import PestanaPresupuestos, PestanaNuevoPresupuesto
from ui.modules.inicio.tab_inicio import PestanaInicio

class TarjetaOperacionSidebar(QFrame):
    clicked = pyqtSignal()
    cerrar_solicitado = pyqtSignal()

    def __init__(self, id_op):
        super().__init__()
        self.id_op = id_op
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(50)
        self.setObjectName("tarjeta_op")
        
        # Estado
        self.colapsada = False
        self.seleccionada = False
        self.tipo = "VENTA"
        
        self.layout_principal = QHBoxLayout(self)
        self.layout_principal.setContentsMargins(8, 4, 8, 4)
        self.layout_principal.setSpacing(8)
        
        # Icono
        self.lbl_icono = QLabel("🛒")
        self.lbl_icono.setStyleSheet("font-size: 16px; background: transparent; border: none;")
        self.lbl_icono.setFixedSize(24, 24)
        self.lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Textos
        self.contenedor_textos = QWidget()
        ly_textos = QVBoxLayout(self.contenedor_textos)
        ly_textos.setContentsMargins(0, 0, 0, 0)
        ly_textos.setSpacing(0)
        
        self.lbl_titulo = QLabel("Venta")
        self.lbl_titulo.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: bold;")
        
        self.lbl_detalle = QLabel("Cons. Final")
        self.lbl_detalle.setStyleSheet("color: #94a3b8; font-size: 11px;")
        
        ly_textos.addWidget(self.lbl_titulo)
        ly_textos.addWidget(self.lbl_detalle)
        
        # Botón cerrar
        self.btn_cerrar = QPushButton("✕")
        self.btn_cerrar.setFixedSize(20, 20)
        self.btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar.setStyleSheet("QPushButton { color: #94a3b8; background: transparent; border: none; font-size: 14px; font-weight: bold; padding-bottom: 2px; } QPushButton:hover { color: #ef4444; }")
        self.btn_cerrar.clicked.connect(self.cerrar_solicitado.emit)
        
        self.layout_principal.addWidget(self.lbl_icono, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.layout_principal.addWidget(self.contenedor_textos, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.layout_principal.addStretch()
        self.layout_principal.addWidget(self.btn_cerrar, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.actualizar_estilo()

    def actualizar_estilo(self):
        bg = "#1e293b" if self.seleccionada else "transparent"
        border = "border-left: 3px solid #3b82f6;" if self.seleccionada else "border-left: 3px solid transparent;"
        hover = "QFrame#tarjeta_op:hover { background-color: #1e293b; }"
        self.setStyleSheet(f"QFrame#tarjeta_op {{ background-color: {bg}; {border} border-radius: 4px; }} {hover}")
        
    def set_seleccionada(self, sel):
        self.seleccionada = sel
        self.actualizar_estilo()
        
    def set_colapsada(self, colapsada):
        self.colapsada = colapsada
        self.contenedor_textos.setVisible(not colapsada)
        self.btn_cerrar.setVisible(not colapsada)
        self.setToolTip(self.lbl_titulo.text() + " - " + self.lbl_detalle.text() if colapsada else "")
        
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.clicked.emit()
        
    def actualizar_datos(self, datos):
        self.tipo = datos.get('tipo', 'VENTA')
        is_edicion = datos.get('is_edicion', False)
        
        if is_edicion:
            icono = "✏️"
            txt_tipo = f"Edición P-{datos.get('id_presupuesto_edicion', '')}"
        elif self.tipo == 'PRESUPUESTO':
            icono = "📄"
            txt_tipo = "Presupuesto"
        else:
            icono = "🛒"
            txt_tipo = "Venta"
            
        self.lbl_icono.setText(icono)
        self.lbl_titulo.setText(txt_tipo)
        
        cliente = datos.get('cliente')
        nombre = cliente['nombre'] if cliente else "Cons. Final"
        
        items = datos.get('items', 0)
        total = datos.get('total', 0.0)
        
        from ui.components.operacion_base import formato_arg
        
        if items > 0:
            self.lbl_detalle.setText(f"{nombre} ({items} it. $ {formato_arg(total)})")
        else:
            self.lbl_detalle.setText(nombre)
            
        if self.colapsada:
            self.setToolTip(f"{txt_tipo} - {self.lbl_detalle.text()}")

class SidebarButton(QPushButton):
    def __init__(self, tipo_icono, texto):
        super().__init__()
        self.tipo_icono = tipo_icono
        self.texto = texto
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(46)
        
        self._hover_progress = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(150)
        self._anim.valueChanged.connect(self._on_hover_change)
        
        self._active_progress = 0.0
        self._active_anim = QVariantAnimation(self)
        self._active_anim.setDuration(150)
        self._active_anim.valueChanged.connect(self._on_active_change)
        
        self.toggled.connect(self._on_toggled)
        
    def _on_hover_change(self, val):
        self._hover_progress = val
        self.update()

    def _on_active_change(self, val):
        self._active_progress = val
        self.update()

    def _on_toggled(self, checked):
        self._active_anim.stop()
        self._active_anim.setStartValue(self._active_progress)
        self._active_anim.setEndValue(1.0 if checked else 0.0)
        self._active_anim.start()
        
    def enterEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self._hover_progress)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(e)
        
    def leaveEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self._hover_progress)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(e)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        margen_x = 10
        # Leve desplazamiento a la derecha según el estado
        offset_x = int(3 * max(self._hover_progress, self._active_progress))
        rect_bg = self.rect().adjusted(margen_x + offset_x, 0, -margen_x + offset_x, 0)
        
        # Color interpolado sin transparencia: #0f172a (base) -> #1e293b (activo/hover)
        # 15, 23, 42 -> 30, 41, 59
        p = max(self._hover_progress, self._active_progress)
        r_bg = 15 + (30 - 15) * p
        g_bg = 23 + (41 - 23) * p
        b_bg = 42 + (59 - 42) * p
        
        if p > 0:
            # Sombra suave (color oscuro sólido para evitar problemas de composición)
            shadow_rect = rect_bg.adjusted(2, 2, 2, 2)
            painter.setBrush(QColor(0, 0, 0, 60))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(shadow_rect, 8, 8)
            
            # Fondo del botón
            painter.setBrush(QColor(int(r_bg), int(g_bg), int(b_bg)))
            painter.drawRoundedRect(rect_bg, 8, 8)
            
        # Borde izquierdo del botón seleccionado
        if self._active_progress > 0:
            ind_h = int((self.height() - 20) * self._active_progress)
            ind_y = int((self.height() - ind_h) / 2)
            painter.setBrush(QColor("#3b82f6")) # COLOR_PRIMARY
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(margen_x + offset_x, ind_y, 4, ind_h, 2, 2)
            
        # Icono y texto 100% opacos SIEMPRE
        color_contenido = QColor("#f8fafc")
        
        # Texto
        espacio_icono = 24
        x_texto = margen_x + offset_x + 46
        
        if self.width() > 90:
            painter.save()
            # Clip para ocultar el texto en la animación de colapso sin usar opacidad
            clip_w = max(0, self.width() - x_texto - margen_x)
            painter.setClipRect(x_texto, 0, clip_w, self.height())
            
            font = self.font()
            font.setPixelSize(14)
            font.setWeight(QFont.Weight.Bold if self.isChecked() else QFont.Weight.Medium)
            font.setFamily("Segoe UI")
            painter.setFont(font)
            
            painter.setPen(color_contenido)
            painter.drawText(x_texto, 0, 200, self.height(), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.texto)
            painter.restore()
            
        # Icono completamente estático en todos los estados
        x_icon = int((65 - espacio_icono) / 2.0)
        y_icon = (self.height() - espacio_icono) // 2
        
        self._draw_icon(painter, x_icon, y_icon, self.tipo_icono, color_contenido)

    def _draw_icon(self, painter, x, y, tipo, color):
        painter.save()
        painter.translate(x, y)
        
        pen = painter.pen()
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setColor(color)
        pen.setWidth(2)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        if tipo == "inicio":
            path = QPainterPath()
            path.moveTo(12, 4)
            path.lineTo(3, 11)
            path.lineTo(3, 20)
            path.lineTo(9, 20)
            path.lineTo(9, 13)
            path.lineTo(15, 13)
            path.lineTo(15, 20)
            path.lineTo(21, 20)
            path.lineTo(21, 11)
            path.closeSubpath()
            painter.drawPath(path)
        elif tipo == "ventas":
            painter.drawRoundedRect(3, 6, 18, 12, 2, 2)
            painter.drawLine(3, 11, 21, 11)
        elif tipo == "stock":
            painter.drawRect(4, 4, 16, 16)
            painter.drawLine(4, 10, 20, 10)
            painter.drawLine(12, 10, 12, 20)
        elif tipo == "clientes":
            painter.drawEllipse(8, 3, 8, 8)
            path = QPainterPath()
            path.moveTo(3, 21)
            path.quadTo(12, 12, 21, 21)
            painter.drawPath(path)
        elif tipo == "presupuestos":
            painter.drawRoundedRect(5, 2, 14, 20, 2, 2)
            painter.drawLine(9, 7, 15, 7)
            painter.drawLine(9, 12, 15, 12)
            painter.drawLine(9, 17, 12, 17)
            
        painter.restore()


class SidebarToggleButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Expandir/Contraer menú")
        
        self._rotation = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.valueChanged.connect(self._on_rotation_change)

        self._hover_progress = 0.0
        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(150)
        self._hover_anim.valueChanged.connect(self._on_hover_change)

    def _on_rotation_change(self, val):
        self._rotation = val
        self.update()
        
    def _on_hover_change(self, val):
        self._hover_progress = val
        self.update()

    def set_colapsada(self, colapsada):
        self._anim.stop()
        self._anim.setStartValue(self._rotation)
        self._anim.setEndValue(90.0 if colapsada else 0.0)
        self._anim.start()

    def enterEvent(self, e):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        super().leaveEvent(e)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        p = self._hover_progress
        if p > 0:
            r_bg = 15 + (30 - 15) * p
            g_bg = 23 + (41 - 23) * p
            b_bg = 42 + (59 - 42) * p
            painter.setBrush(QColor(int(r_bg), int(g_bg), int(b_bg)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 6, 6)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._rotation)
        
        font = self.font()
        font.setPixelSize(20)
        painter.setFont(font)
        
        painter.setPen(QColor("#f8fafc"))
        
        rect = self.rect()
        rect.translate(-rect.width() // 2, -rect.height() // 2)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "☰")


class VentanaPrincipal(QMainWindow):
    def __init__(self, conexion_db):
        super().__init__()
        self.conn = conexion_db
        self.setWindowTitle("ConstruSecoPereyra")
        # El tamaño inicial ahora está controlado por el sistema para arrancar maximizado

        # Forzamos el fondo claro en la ventana contenedora principal
        self.setStyleSheet("""
            QMainWindow { background-color: #f8fafc; }
            QToolTip {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #3b82f6;
                border-radius: 4px;
                padding: 5px 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: bold;
            }
        """)

        # Configuración para recordar estado
        self.settings = QSettings("ConstruSeco", "ERP")
        self.sidebar_colapsada = self.settings.value("sidebar_colapsada", False, type=bool)
        
        # Inicializamos estado para operaciones abiertas
        self.operaciones_abiertas = {} # {id_operacion: (widget, tarjeta)}
        self.siguiente_id_operacion = 1

        self.init_ui()

    def init_ui(self):
        # Componente central que divide la pantalla en dos (Izquierda: Menú, Derecha: Contenido)
        widget_central = QWidget()
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)  # Sin bordes exteriores
        layout_principal.setSpacing(0)

        # 1. BARRA LATERAL (SIDEBAR)
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(230)
        # Aplicamos un estilo gris oscuro/azulado corporativo para la barra lateral
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #0f172a; /* Azul noche oscuro */
                border: none;
            }
        """)

        layout_sidebar = QVBoxLayout(self.sidebar)
        layout_sidebar.setContentsMargins(0, 0, 0, 0)
        layout_sidebar.setSpacing(2)

        # Botón Toggle
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(15, 10, 15, 0)
        self.btn_toggle = SidebarToggleButton()
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        top_layout.addWidget(self.btn_toggle, 0, Qt.AlignmentFlag.AlignLeft)
        top_layout.addStretch()
        layout_sidebar.addLayout(top_layout)

        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Intentamos cargar la imagen (si no existe, simplemente queda el espacio vacío)
        try:
            # Ruta robusta al logo, basada en la ubicación real de este archivo
            _logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
            pixmap = QPixmap(str(_logo_path)).scaled(
                90, 90,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_logo.setPixmap(pixmap)
            self.lbl_logo.setContentsMargins(0, 20, 0, 0)
        except Exception:
            print("Logo no encontrado todavía, usando espacio vacío.")

        # ENCABEZADO MODERNO
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(10, 5, 10, 25)
        header_layout.setSpacing(4)

        self.lbl_marca = QLabel("ConstruSeco ERP")
        self.lbl_marca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_marca.setStyleSheet("""
           QLabel {
                color: #f8fafc;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 16px;
                font-weight: 700;
            }
        """)

        self.lbl_sub = QLabel("Sistema de Gestión Comercial")
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sub.setStyleSheet("""
           QLabel {
                color: #64748b;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 10px;
                font-weight: 500;
            }
        """)

        header_layout.addWidget(self.lbl_marca)
        header_layout.addWidget(self.lbl_sub)

        # Agregamos el logo y el texto a la barra lateral
        layout_sidebar.addWidget(self.lbl_logo)
        layout_sidebar.addWidget(header_container)

        # Creamos los botones del menú usando la nueva clase custom
        self.btn_inicio = SidebarButton("inicio", "Inicio")
        self.btn_ventas = SidebarButton("ventas", "Venta")
        self.btn_stock = SidebarButton("stock", "Control de Stock")
        self.btn_clientes = SidebarButton("clientes", "Clientes")
        self.btn_presupuestos = SidebarButton("presupuestos", "Presupuestos")

        # Agrupamos los botones para que actúen en conjunto
        self.botones_menu = [self.btn_inicio, self.btn_ventas, self.btn_stock, self.btn_clientes, self.btn_presupuestos]
        for btn in self.botones_menu:
            layout_sidebar.addWidget(btn)

        # Resorte inferior invisible para empujar los botones principales hacia arriba si hace falta
        # layout_sidebar.addStretch() # Quitado para que la lista de operaciones crezca.
        # SECCIÓN EN CURSO
        ly_en_curso = QHBoxLayout()
        ly_en_curso.setContentsMargins(15, 10, 15, 10)
        self.lbl_en_curso = QLabel("EN CURSO")
        self.lbl_en_curso.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        
        self.btn_nueva_op = QPushButton("＋")
        self.btn_nueva_op.setFixedSize(22, 22)
        self.btn_nueva_op.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nueva_op.setStyleSheet("""
            QPushButton { 
                color: #64748b; 
                background: transparent; 
                border: none; 
                border-radius: 4px; 
                font-weight: 800; 
                font-size: 14px;
                padding: 0;
                margin: 0;
            } 
            QPushButton:hover { 
                background: #e2e8f0; 
                color: #0f172a;
            }
            QPushButton::menu-indicator {
                image: none;
                width: 0px;
            }
        """)
        
        self.menu_nueva_op = QMenu(self)
        self.menu_nueva_op.setStyleSheet("QMenu { background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; } QMenu::item:selected { background-color: #3b82f6; }")
        
        accion_venta = self.menu_nueva_op.addAction("🛒 Venta Rápida")
        accion_venta.triggered.connect(lambda: self.crear_operacion("VENTA"))
        
        accion_presup = self.menu_nueva_op.addAction("📄 Nuevo Presupuesto")
        accion_presup.triggered.connect(lambda: self.crear_operacion("PRESUPUESTO"))
        
        self.btn_nueva_op.clicked.connect(lambda: self.menu_nueva_op.exec(self.btn_nueva_op.mapToGlobal(self.btn_nueva_op.rect().bottomLeft())))
        
        ly_en_curso.addWidget(self.lbl_en_curso, alignment=Qt.AlignmentFlag.AlignVCenter)
        ly_en_curso.addStretch()
        ly_en_curso.addWidget(self.btn_nueva_op, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        layout_sidebar.addLayout(ly_en_curso)
        
        # Scroll para tarjetas
        scroll_tarjetas = QScrollArea()
        scroll_tarjetas.setWidgetResizable(True)
        scroll_tarjetas.setFrameShape(QFrame.Shape.NoFrame)
        scroll_tarjetas.setStyleSheet("background: transparent;")
        
        content_tarjetas = QWidget()
        content_tarjetas.setStyleSheet("background: transparent;")
        self.layout_tarjetas = QVBoxLayout(content_tarjetas)
        self.layout_tarjetas.setContentsMargins(10, 5, 10, 5)
        self.layout_tarjetas.setSpacing(4)
        self.layout_tarjetas.addStretch() # Empuja hacia arriba
        
        scroll_tarjetas.setWidget(content_tarjetas)
        layout_sidebar.addWidget(scroll_tarjetas, stretch=1)
        
        # PIE DE LA BARRA
        footer_container = QWidget()
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(10, 10, 10, 20)
        footer_layout.setSpacing(4)
        
        self.lbl_version = QLabel("Versión")
        self.lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_db = QLabel("SQLite")
        self.lbl_db.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        footer_style = """
            QLabel {
                color: #334155;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 9px;
            }
        """
        self.lbl_version.setStyleSheet(footer_style)
        self.lbl_db.setStyleSheet(footer_style)
        
        footer_layout.addWidget(self.lbl_version)
        footer_layout.addWidget(self.lbl_db)
        
        layout_sidebar.addWidget(footer_container)

        # 2. CONTENEDOR DE PESTAÑAS (DERECHA)
        self.contenedor_vistas = QStackedWidget()

        # Instanciamos las pestañas fijas
        self.pestana_inicio = PestanaInicio(self.conn)
        self.pestana_stock     = PestanaStock(self.conn)
        self.pestana_clientes  = PestanaClientes(self.conn)
        self.pestana_historial_presupuestos = PestanaPresupuestos(self.conn)

        # Agregamos las vistas fijas al mazo de cartas (QStackedWidget)
        self.contenedor_vistas.addWidget(self.pestana_inicio)
        self.contenedor_vistas.addWidget(self.pestana_stock)             
        self.contenedor_vistas.addWidget(self.pestana_clientes)          
        self.contenedor_vistas.addWidget(self.pestana_historial_presupuestos)   

        # Enlazamos los clics de los botones de navegación principal
        self.btn_inicio.clicked.connect(lambda: self.cambiar_pestana_fija(self.pestana_inicio, self.btn_inicio))
        self.btn_ventas.clicked.connect(self._navegar_ventas)
        self.btn_stock.clicked.connect(lambda: self.cambiar_pestana_fija(self.pestana_stock, self.btn_stock))
        self.btn_clientes.clicked.connect(lambda: self.cambiar_pestana_fija(self.pestana_clientes, self.btn_clientes))
        self.btn_presupuestos.clicked.connect(lambda: self.cambiar_pestana_fija(self.pestana_historial_presupuestos, self.btn_presupuestos))
        
        # Conectamos señales de la pestaña de inicio
        self.pestana_inicio.nueva_venta_solicitada.connect(lambda: self.crear_operacion("VENTA"))
        self.pestana_inicio.nuevo_presupuesto_solicitado.connect(lambda: self.crear_operacion("PRESUPUESTO"))
        self.pestana_inicio.ver_stock_solicitado.connect(lambda: self.cambiar_pestana_fija(self.pestana_stock, self.btn_stock))
        self.pestana_inicio.ver_clientes_solicitado.connect(lambda: self.cambiar_pestana_fija(self.pestana_clientes, self.btn_clientes))
        self.pestana_inicio.ver_presupuestos_solicitado.connect(lambda: self.cambiar_pestana_fija(self.pestana_historial_presupuestos, self.btn_presupuestos))

        # Ensamblamos todo en la ventana central
        layout_principal.addWidget(self.sidebar)
        layout_principal.addWidget(self.contenedor_vistas)

        self.setCentralWidget(widget_central)
        
        # Aplicar estado inicial de la sidebar sin animar (Forzamos colapsado para la vista Inicio)
        self.sidebar_colapsada = True
        self.actualizar_estado_sidebar(animar=False)
        
        # Iniciar timer operativo global y limpiar vencidos
        self._timer_limpieza = QTimer(self)
        self._timer_limpieza.timeout.connect(self._verificar_y_limpiar_vencidos)
        self._timer_limpieza.start(300_000)
        QTimer.singleShot(1000, self._verificar_y_limpiar_vencidos)
        
        # Abrimos la pestaña inicio por defecto
        QTimer.singleShot(0, lambda: self.cambiar_pestana_fija(self.pestana_inicio, self.btn_inicio))

    def toggle_sidebar(self):
        self.sidebar_colapsada = not self.sidebar_colapsada
        self.settings.setValue("sidebar_colapsada", self.sidebar_colapsada)
        self.actualizar_estado_sidebar(animar=True)

    def actualizar_estado_sidebar(self, animar=False):
        ancho_objetivo = 65 if self.sidebar_colapsada else 230
        
        # Visibilidad de textos y botones
        self.lbl_marca.setVisible(not self.sidebar_colapsada)
        self.lbl_sub.setVisible(not self.sidebar_colapsada)
        self.lbl_version.setVisible(not self.sidebar_colapsada)
        self.lbl_db.setVisible(not self.sidebar_colapsada)
        self.lbl_en_curso.setVisible(not self.sidebar_colapsada)
        if hasattr(self, 'btn_nueva_op'):
            self.btn_nueva_op.setVisible(not self.sidebar_colapsada)
        
        # Tamaño del logo
        size_logo = 40 if self.sidebar_colapsada else 90
        try:
            _logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
            pixmap = QPixmap(str(_logo_path)).scaled(
                size_logo, size_logo,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_logo.setPixmap(pixmap)
            margen_top = 10 if self.sidebar_colapsada else 20
            self.lbl_logo.setContentsMargins(0, margen_top, 0, 0)
        except Exception:
            pass

        # Tooltips de los botones
        for btn in self.botones_menu:
            btn.setToolTip(btn.texto if self.sidebar_colapsada else "")
            
        self.btn_nueva_op.setToolTip("Nueva Operación" if self.sidebar_colapsada else "")
        
        # Actualizar tarjetas
        if hasattr(self, 'operaciones_abiertas'):
            for id_op, (w, t) in self.operaciones_abiertas.items():
                t.set_colapsada(self.sidebar_colapsada)
            
        # Actualizar estado de rotación del botón hamburguesa
        if isinstance(self.btn_toggle, SidebarToggleButton):
            if not animar:
                self.btn_toggle._rotation = 90.0 if self.sidebar_colapsada else 0.0
                self.btn_toggle.update()
            else:
                self.btn_toggle.set_colapsada(self.sidebar_colapsada)

        if animar:
            self.anim_min = QPropertyAnimation(self.sidebar, b"minimumWidth")
            self.anim_min.setDuration(200)
            self.anim_min.setStartValue(self.sidebar.width())
            self.anim_min.setEndValue(ancho_objetivo)
            self.anim_min.setEasingCurve(QEasingCurve.Type.InOutQuad)
            
            self.anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth")
            self.anim_max.setDuration(200)
            self.anim_max.setStartValue(self.sidebar.width())
            self.anim_max.setEndValue(ancho_objetivo)
            self.anim_max.setEasingCurve(QEasingCurve.Type.InOutQuad)
            
            self.anim_min.start()
            self.anim_max.start()
            
            # Guardamos referencia para evitar recolección de basura
            self._anims = [self.anim_min, self.anim_max]
        else:
            self.sidebar.setMinimumWidth(ancho_objetivo)
            self.sidebar.setMaximumWidth(ancho_objetivo)

    def _verificar_y_limpiar_vencidos(self):
        from db.conexion import limpiar_presupuestos_vencidos
        afectados = limpiar_presupuestos_vencidos(self.conn)
        if afectados and afectados > 0:
            self.notificar_cambios(["PRESUPUESTOS", "STOCK"])

    def _navegar_ventas(self):
        # Buscar la última venta activa si la hay, si no crear una.
        ultima_op = None
        for id_op, (w, t) in self.operaciones_abiertas.items():
            if t.tipo == "VENTA":
                ultima_op = id_op
            
        if ultima_op is not None:
            self.seleccionar_operacion(ultima_op)
        else:
            self.crear_operacion("VENTA")

    def crear_operacion(self, tipo="VENTA", is_edicion=False, id_edicion=None):
        id_op = self.siguiente_id_operacion
        self.siguiente_id_operacion += 1
        
        if is_edicion or tipo == "PRESUPUESTO":
            widget = PestanaNuevoPresupuesto(self.conn, is_edicion=is_edicion, id_presupuesto_edicion=id_edicion)
        else:
            widget = PestanaNuevaVenta(self.conn)
            
        tarjeta = TarjetaOperacionSidebar(id_op)
        tarjeta.set_colapsada(self.sidebar_colapsada)
        
        tarjeta.clicked.connect(lambda: self.seleccionar_operacion(id_op))
        tarjeta.cerrar_solicitado.connect(lambda: self.cerrar_operacion(id_op))
        
        widget.estado_cambiado.connect(tarjeta.actualizar_datos)
        widget.operacion_completada.connect(lambda _: self._on_operacion_completada(id_op))
        
        self.operaciones_abiertas[id_op] = (widget, tarjeta)
        
        self.contenedor_vistas.addWidget(widget)
        self.layout_tarjetas.insertWidget(self.layout_tarjetas.count() - 1, tarjeta)
        
        tarjeta.actualizar_datos({'tipo': tipo, 'items': 0, 'total': 0.0, 'is_edicion': is_edicion, 'id_presupuesto_edicion': id_edicion})
        
        self.seleccionar_operacion(id_op)

    def seleccionar_operacion(self, id_op):
        if id_op not in self.operaciones_abiertas: return
        widget, tarjeta = self.operaciones_abiertas[id_op]
        
        for op, (w, t) in self.operaciones_abiertas.items():
            t.set_seleccionada(op == id_op)
            
        for btn in self.botones_menu:
            btn.setChecked(False)
            btn.update()
            
        if tarjeta.tipo == "VENTA":
            self.btn_ventas.setChecked(True)
            self.btn_ventas.update()
        elif tarjeta.tipo == "PRESUPUESTO":
            self.btn_presupuestos.setChecked(True)
            self.btn_presupuestos.update()
            
        self._transicion_vista(widget)

    def cerrar_operacion(self, id_op, forzar=False):
        if id_op not in self.operaciones_abiertas: return
        widget, tarjeta = self.operaciones_abiertas[id_op]
        
        if not forzar and not widget.esta_vacia():
            res = QMessageBox.question(self, "Cerrar Operación", "¿Seguro que desea cerrar esta operación? Se perderán los ítems cargados.")
            if res != QMessageBox.StandardButton.Yes:
                return
                
        self.contenedor_vistas.removeWidget(widget)
        widget.deleteLater()
        self.layout_tarjetas.removeWidget(tarjeta)
        tarjeta.deleteLater()
        
        del self.operaciones_abiertas[id_op]
        
        # Si cerramos la actual, ir a la última o a stock
        if self.contenedor_vistas.currentWidget() == widget:
            if self.operaciones_abiertas:
                self.seleccionar_operacion(list(self.operaciones_abiertas.keys())[-1])
            else:
                self.cambiar_pestana_fija(self.pestana_stock, self.btn_stock)

    def _on_operacion_completada(self, id_op):
        self.cerrar_operacion(id_op, forzar=True)
        self.notificar_cambios(["STOCK", "CLIENTES", "PRESUPUESTOS"])

    def actualizar_catalogos_operaciones(self):
        for id_op, (widget, tarjeta) in self.operaciones_abiertas.items():
            if hasattr(widget, 'cargar_catalogo_memoria'):
                widget.cargar_catalogo_memoria()

    def notificar_cambios(self, modulos):
        """
        Sistema centralizado de eventos para refrescar la UI.
        Recibe una lista de módulos afectados, ej: ['STOCK', 'CLIENTES']
        """
        if "STOCK" in modulos:
            if hasattr(self, 'pestana_stock'):
                self.pestana_stock.cargar_datos()
        if "CLIENTES" in modulos:
            if hasattr(self, 'pestana_clientes'):
                self.pestana_clientes.recargar()
        if "PRESUPUESTOS" in modulos:
            if hasattr(self, 'pestana_historial_presupuestos'):
                self.pestana_historial_presupuestos.recargar()
        
        # Inicio actualiza sus tarjetas siempre
        if hasattr(self, 'pestana_inicio'):
            self.pestana_inicio.cargar_datos()
            
        # Recargar operaciones (Ventas/Presupuestos nuevos)
        self.actualizar_catalogos_operaciones()


    def cambiar_pestana_fija(self, widget, boton_presionado):
        for op, (w, t) in self.operaciones_abiertas.items():
            t.set_seleccionada(False)
            
        for btn in self.botones_menu:
            btn.setChecked(btn == boton_presionado)
            btn.update()
            
        self._transicion_vista(widget)

    def _transicion_vista(self, widget):
        estado_previo = self.sidebar_colapsada
        if widget == getattr(self, 'pestana_inicio', None):
            self.sidebar_colapsada = True
        else:
            self.sidebar_colapsada = False
            
        if estado_previo != self.sidebar_colapsada:
            self.actualizar_estado_sidebar(animar=True)
            
        if self.contenedor_vistas.currentWidget() == widget:
            self._aplicar_foco(widget)
            return
            
        self.fade_effect = QGraphicsOpacityEffect(self.contenedor_vistas)
        self.contenedor_vistas.setGraphicsEffect(self.fade_effect)
        self.fade_anim = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_anim.setDuration(250)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.contenedor_vistas.setCurrentWidget(widget)
        self.fade_anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self.fade_anim.finished.connect(lambda: self._on_transition_finished(widget))

    def _on_transition_finished(self, widget):
        self.contenedor_vistas.setGraphicsEffect(None)
        self._aplicar_foco(widget)

    def _aplicar_foco(self, widget):
        if hasattr(widget, 'input_buscador'):
            widget.input_buscador.setFocus()
        elif hasattr(widget, 'input_busqueda'):
            widget.input_busqueda.setFocus()
