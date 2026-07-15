from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from pathlib import Path
from ui.modules.stock.tab_stock import PestanaStock
from ui.modules.ventas.tab_ventas import PestanaNuevaVenta
from ui.modules.clientes.tab_clientes import PestanaClientes
from ui.modules.presupuestos.tab_presupuestos import PestanaPresupuestos


class VentanaPrincipal(QMainWindow):
    def __init__(self, conexion_db):
        super().__init__()
        self.conn = conexion_db
        self.setWindowTitle("ConstruSecoPereyra")
        # El tamaño inicial ahora está controlado por el sistema para arrancar maximizado

        # Forzamos el fondo claro en la ventana contenedora principal
        self.setStyleSheet("QMainWindow { background-color: #f8fafc; }")

        self.init_ui()

    def init_ui(self):
        # Componente central que divide la pantalla en dos (Izquierda: Menú, Derecha: Contenido)
        widget_central = QWidget()
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)  # Sin bordes exteriores
        layout_principal.setSpacing(0)

        # 1. BARRA LATERAL (SIDEBAR)
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        # Aplicamos un estilo gris oscuro/azulado corporativo para la barra lateral
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #0f172a; /* Azul noche oscuro */
                border: none;
            }
            QLabel {
                color: #f1f5f9;
                font-size: 18px;
                font-weight: bold;
                padding: 20px 10px;
            }
            QPushButton {
                background-color: transparent;
                color: #94a3b8; /* Gris suave */
                text-align: left;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                border: none;
                border-left: 4px solid transparent;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #f8fafc;
            }
            QPushButton:checked {
                background-color: #1e293b;
                color: #3b82f6; /* Texto azul brillante al estar activo */
                border-left: 4px solid #3b82f6; /* Línea indicadora azul a la izquierda */
                font-weight: bold;
            }
        """)

        layout_sidebar = QVBoxLayout(sidebar)
        layout_sidebar.setContentsMargins(0, 0, 0, 0)
        layout_sidebar.setSpacing(5)

        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Intentamos cargar la imagen (si no existe, simplemente queda el espacio vacío)
        try:
            # Ruta robusta al logo, basada en la ubicación real de este archivo
            _logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
            pixmap = QPixmap(str(_logo_path)).scaled(
                100, 100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_logo.setPixmap(pixmap)
        except Exception:
            print("Logo no encontrado todavía, usando espacio vacío.")

        # Título de la sección superior de la Sidebar
        lbl_marca = QLabel("  Construseco\nPereyra")
        lbl_marca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_marca.setStyleSheet("""
           QLabel {
                color: #f1f5f9;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 19px;
                font-weight: 800;
                margin-top: -10px;
                margin-bottom: 25px;
            }
        """)

        # Agregamos el logo y el texto a la barra lateral
        layout_sidebar.addWidget(self.lbl_logo)
        layout_sidebar.addWidget(lbl_marca)

        # Creamos los botones del menú
        self.btn_ventas = QPushButton(" Venta")
        self.btn_ventas.setCheckable(True)
        self.btn_ventas.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_stock = QPushButton(" Control de Stock")
        self.btn_stock.setCheckable(True)
        self.btn_stock.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_clientes = QPushButton(" Clientes")
        self.btn_clientes.setCheckable(True)
        self.btn_clientes.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_presupuestos = QPushButton(" Presupuestos")
        self.btn_presupuestos.setCheckable(True)
        self.btn_presupuestos.setCursor(Qt.CursorShape.PointingHandCursor)

        # Agrupamos los botones para que actúen en conjunto
        self.botones_menu = [self.btn_ventas, self.btn_stock, self.btn_clientes, self.btn_presupuestos]
        for btn in self.botones_menu:
            layout_sidebar.addWidget(btn)

        # Resorte inferior invisible para empujar los botones hacia arriba
        layout_sidebar.addStretch()

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
        layout_principal.addWidget(sidebar)
        layout_principal.addWidget(self.contenedor_vistas)

        self.setCentralWidget(widget_central)
        
        # Iniciar timer operativo global (Ej: cada 5 min = 300,000 ms)
        self._timer_limpieza = QTimer(self)
        self._timer_limpieza.timeout.connect(self._verificar_y_limpiar_vencidos)
        self._timer_limpieza.start(300_000)
        
        # Hacer una limpieza inicial silenciosa
        QTimer.singleShot(1000, self._verificar_y_limpiar_vencidos)

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
        self.contenedor_vistas.setCurrentIndex(indice)

        # Desmarcar todos los botones excepto el que se presionó
        for btn in self.botones_menu:
            btn.setChecked(btn == boton_presionado)
