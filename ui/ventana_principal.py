from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QFrame,
                             QGraphicsOpacityEffect, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QVariantAnimation, QPropertyAnimation, QEasingCurve, QSettings
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPainterPath
from pathlib import Path
from ui.modules.stock.tab_stock import PestanaStock
from ui.modules.ventas.tab_ventas import PestanaNuevaVenta
from ui.modules.clientes.tab_clientes import PestanaClientes
from ui.modules.presupuestos.tab_presupuestos import PestanaPresupuestos


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
        
        if tipo == "ventas":
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
        self.btn_ventas = SidebarButton("ventas", "Venta")
        self.btn_stock = SidebarButton("stock", "Control de Stock")
        self.btn_clientes = SidebarButton("clientes", "Clientes")
        self.btn_presupuestos = SidebarButton("presupuestos", "Presupuestos")

        # Agrupamos los botones para que actúen en conjunto
        self.botones_menu = [self.btn_ventas, self.btn_stock, self.btn_clientes, self.btn_presupuestos]
        for btn in self.botones_menu:
            layout_sidebar.addWidget(btn)

        # Resorte inferior invisible para empujar los botones hacia arriba
        layout_sidebar.addStretch()
        
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

        # Instanciamos las pestañas reales
        self.vista_ventas_temp = PestanaNuevaVenta(self.conn)        # Índice 0
        self.pestana_stock     = PestanaStock(self.conn)             # Índice 1
        self.pestana_clientes  = PestanaClientes(self.conn)          # Índice 2

        self.vista_presupuestos_temp = PestanaPresupuestos(self.conn)

        # Agregamos las vistas al mazo de cartas (QStackedWidget)
        self.contenedor_vistas.addWidget(self.vista_ventas_temp)         # Índice 0
        self.contenedor_vistas.addWidget(self.pestana_stock)             # Índice 1
        self.contenedor_vistas.addWidget(self.pestana_clientes)          # Índice 2
        self.contenedor_vistas.addWidget(self.vista_presupuestos_temp)   # Índice 3

        # Enlazamos los clics de los botones para cambiar de pestaña dinámicamente
        self.btn_ventas.clicked.connect(lambda: self.cambiar_pestana(0, self.btn_ventas))
        self.btn_stock.clicked.connect(lambda: self.cambiar_pestana(1, self.btn_stock))
        self.btn_clientes.clicked.connect(lambda: self.cambiar_pestana(2, self.btn_clientes))
        self.btn_presupuestos.clicked.connect(lambda: self.cambiar_pestana(3, self.btn_presupuestos))

        # Dejar la primera pestaña (Ventas) seleccionada por defecto al abrir
        self.cambiar_pestana(0, self.btn_ventas)

        # Ensamblamos todo en la ventana central
        layout_principal.addWidget(self.sidebar)
        layout_principal.addWidget(self.contenedor_vistas)

        self.setCentralWidget(widget_central)
        
        # Aplicar estado inicial de la sidebar sin animar
        self.actualizar_estado_sidebar(animar=False)
        
        # Iniciar timer operativo global (Ej: cada 5 min = 300,000 ms)
        self._timer_limpieza = QTimer(self)
        self._timer_limpieza.timeout.connect(self._verificar_y_limpiar_vencidos)
        self._timer_limpieza.start(300_000)
        
        # Hacer una limpieza inicial silenciosa
        QTimer.singleShot(1000, self._verificar_y_limpiar_vencidos)

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
        except:
            pass

        # Tooltips de los botones
        for btn in self.botones_menu:
            btn.setToolTip(btn.texto if self.sidebar_colapsada else "")
            
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
            # Recargar Presupuestos para reflejar cambios (vencidos) sin perder selección
            self.vista_presupuestos_temp.recargar()
            
            # Recargar Stock para que el catálogo refleje el ATP liberado
            self.pestana_stock.cargar_datos()
            
            # Recargar catálogo en memoria de la pantalla de Venta/Presupuesto
            self.vista_ventas_temp.cargar_catalogo_memoria()

    def cambiar_pestana(self, indice, boton_presionado):
        """Cambia la vista del contenedor de la derecha y actualiza el botón activo en la barra lateral."""
        if self.contenedor_vistas.currentIndex() == indice and boton_presionado.isChecked():
            return
            
        # Desmarcar todos los botones excepto el que se presionó
        for btn in self.botones_menu:
            btn.setChecked(btn == boton_presionado)
            btn.update()
            
        # Transición sutil (fade)
        self.fade_effect = QGraphicsOpacityEffect(self.contenedor_vistas)
        self.contenedor_vistas.setGraphicsEffect(self.fade_effect)
        
        self.fade_anim = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_anim.setDuration(250)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.contenedor_vistas.setCurrentIndex(indice)
        
        self.fade_anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self.fade_anim.finished.connect(lambda: self.contenedor_vistas.setGraphicsEffect(None))
