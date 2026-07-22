from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from datetime import datetime
from ui.core.theme import COLOR_PRIMARY, COLOR_CARD_BG, COLOR_BORDER, COLOR_TEXT_MAIN, COLOR_TEXT_SEC
from db.queries import obtener_productos_frecuentes

def fecha_formateada():
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    hoy = datetime.now()
    return f"{dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month - 1]} de {hoy.year}"

class TarjetaAtajo(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, icono, titulo, descripcion):
        super().__init__()
        self.setObjectName("tarjeta_blanca")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(f"""
            QFrame#tarjeta_blanca {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            QFrame#tarjeta_blanca:hover {{
                border: 1px solid {COLOR_PRIMARY};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        lbl_icono = QLabel(icono)
        lbl_icono.setStyleSheet("font-size: 32px;")
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 16px; font-weight: bold;")
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
    
    def __init__(self, conexion_db):
        super().__init__()
        self.conn = conexion_db
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Encabezado
        lbl_saludo = QLabel("👋 ¡Bienvenido de nuevo!")
        lbl_saludo.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 28px; font-weight: bold;")
        lbl_fecha = QLabel(fecha_formateada())
        lbl_fecha.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 14px;")
        
        layout.addWidget(lbl_saludo)
        layout.addWidget(lbl_fecha)
        layout.addSpacing(20)
        
        # Atajos
        layout_atajos = QHBoxLayout()
        layout_atajos.setSpacing(15)
        
        atajo_venta = TarjetaAtajo("🛒", "Nueva Venta", "Iniciar una venta rápida")
        atajo_venta.clicked.connect(self.nueva_venta_solicitada.emit)
        
        atajo_presupuesto = TarjetaAtajo("📄", "Nuevo Presupuesto", "Crear cotización")
        atajo_presupuesto.clicked.connect(self.nuevo_presupuesto_solicitado.emit)
        
        atajo_stock = TarjetaAtajo("📦", "Ver Stock", "Consultar inventario")
        atajo_stock.clicked.connect(self.ver_stock_solicitado.emit)
        
        atajo_clientes = TarjetaAtajo("👥", "Ver Clientes", "Gestionar agenda")
        atajo_clientes.clicked.connect(self.ver_clientes_solicitado.emit)
        
        layout_atajos.addWidget(atajo_venta)
        layout_atajos.addWidget(atajo_presupuesto)
        layout_atajos.addWidget(atajo_stock)
        layout_atajos.addWidget(atajo_clientes)
        
        layout.addLayout(layout_atajos)
        layout.addSpacing(30)
        
        # Más vendidos
        lbl_titulo_vendidos = QLabel("📈 Productos más vendidos (últimos 30 días)")
        lbl_titulo_vendidos.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 18px; font-weight: bold;")
        layout.addWidget(lbl_titulo_vendidos)
        
        self.frame_vendidos = QFrame()
        self.frame_vendidos.setObjectName("tarjeta_blanca")
        self.frame_vendidos.setStyleSheet(f"""
            QFrame#tarjeta_blanca {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
        """)
        
        layout_vendidos = QHBoxLayout(self.frame_vendidos)
        layout_vendidos.setContentsMargins(15, 15, 15, 15)
        layout_vendidos.setSpacing(15)
        
        productos_frecuentes = obtener_productos_frecuentes(self.conn)
        
        if productos_frecuentes:
            for p in productos_frecuentes:
                card_prod = QFrame()
                ly_card = QVBoxLayout(card_prod)
                
                lbl_desc = QLabel(p['descripcion'])
                lbl_desc.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: bold; font-size: 14px;")
                lbl_desc.setWordWrap(True)
                
                lbl_codigo = QLabel(f"Código: {p['codigo']}")
                lbl_codigo.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px;")
                
                lbl_vendidos = QLabel(f"Vendidos: {p['vendido']} {p['unidad_base']}")
                lbl_vendidos.setStyleSheet(f"color: {COLOR_PRIMARY}; font-size: 13px; font-weight: bold;")
                
                ly_card.addWidget(lbl_desc)
                ly_card.addWidget(lbl_codigo)
                ly_card.addWidget(lbl_vendidos)
                
                layout_vendidos.addWidget(card_prod)
        else:
            lbl_vacio = QLabel("No hay suficientes datos de ventas recientes.")
            lbl_vacio.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 14px;")
            lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_vendidos.addWidget(lbl_vacio)
            
        layout.addWidget(self.frame_vendidos)
        
        layout.addStretch()
