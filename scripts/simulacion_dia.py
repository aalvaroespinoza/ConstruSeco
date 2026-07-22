import sys
sys.stdout.reconfigure(line_buffering=True)
import os
import sqlite3
import traceback
from datetime import datetime

# Añadir el directorio raíz al path para poder importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QTimer

from ui.ventana_principal import VentanaPrincipal
from ui.core.modal import DialogoModalIntegrado

def mock_exec(*args, **kwargs):
    print("[MOCK] Dialogo ejecutado y aceptado automáticamente.")
    return QDialog.DialogCode.Accepted

def mock_msg(parent, title, text, *args, **kwargs):
    print(f"[MOCK MSG] {title}: {text}")
    return QMessageBox.StandardButton.Ok

QDialog.exec = mock_exec
from ui.core.modal import DialogoModalIntegrado
DialogoModalIntegrado.exec = mock_exec
QMessageBox.warning = mock_msg
QMessageBox.critical = mock_msg
QMessageBox.information = mock_msg

from PyQt6.QtWidgets import QFileDialog
def mock_file_dialog(*args, **kwargs):
    print("[MOCK] Guardando PDF simulado")
    return ("simulado.pdf", "PDF")
QFileDialog.getSaveFileName = mock_file_dialog

def simular_jornada():
    app = QApplication(sys.argv)
    
    print("=== INICIANDO SIMULADOR ===")
    
    conn = sqlite3.connect('corralon_profesional.db')
    
    try:
        window = VentanaPrincipal(conn)
        window.showMaximized()
        
        print("1. Navegando a Stock...")
        window.btn_stock.click()
        QTest.qWait(100)
        
        print("2. Buscando en Stock...")
        window.pestana_stock.input_buscar.setText("cemento")
        QTest.qWait(500) # timer debounce
        
        print("3. Navegando a Clientes...")
        window.btn_clientes.click()
        QTest.qWait(100)
        
        print("4. Abriendo nuevo presupuesto...")
        window.crear_operacion('PRESUPUESTO')
        id_op = window.siguiente_id_operacion - 1
        op_widget = window.operaciones_abiertas[id_op][0]
        op_widget.tipo_documento_seleccionado = 'PRESUPUESTO'
        
        print("5. Agregando producto al carrito directamente...")
        if len(op_widget.catalogo) > 0:
            producto = op_widget.catalogo[0]
            op_widget.seleccionar_producto(producto)
            op_widget.input_cantidad.setText("10")
            op_widget.agregar_al_carrito()
            print(f"Producto {producto['codigo']} agregado.")
        else:
            print("AVISO: No hay productos en catálogo.")
            
        print("6. Confirmando presupuesto...")
        op_widget.confirmar_operacion('PRESUPUESTO')
        
        for _ in range(3):
            # 1. Crear Cliente
            window.btn_clientes.click()
            window.pestana_clientes._on_nuevo_cliente()
            from ui.modules.clientes.dialogs_clientes import DialogoFormularioCliente
            dlg_cli = DialogoFormularioCliente(conn)
            dlg_cli._campos['nombre_completo'].widget.setText("Cliente Bucle")
            dlg_cli._guardar()
            
            # 2. Venta
            window.crear_operacion('VENTA')
            id_op_v = window.siguiente_id_operacion - 1
            op_v = window.operaciones_abiertas[id_op_v][0]
            op_v.tipo_documento_seleccionado = 'VENTA'
            if len(op_v.catalogo) > 0:
                op_v.seleccionar_producto(op_v.catalogo[0])
                op_v.input_cantidad.setText("1")
                op_v.agregar_al_carrito()
                op_v.confirmar_operacion('VENTA')
            
            # 3. Cancelar Presupuesto
            window.crear_operacion('PRESUPUESTO')
            id_op_p = window.siguiente_id_operacion - 1
            op_p = window.operaciones_abiertas[id_op_p][0]
            window.cerrar_operacion(id_op_p)
            
            # 4. Exportar PDF
            window.btn_presupuestos.click()
            if window.pestana_historial_presupuestos._tabla.rowCount() > 0:
                id_doc = window.pestana_historial_presupuestos._tabla.item(0, 0).data(Qt.ItemDataRole.UserRole)
                window.pestana_historial_presupuestos._generar_pdf(id_doc)
                
            # 5. Volver a stock y buscar
            window.btn_stock.click()
            window.pestana_stock.input_buscar.setText("PINTURA")
            QTest.qWait(50)
            
        print("=== SIMULACION EXTENSA COMPLETADA SIN CRASH ===")
    except Exception as e:
        print("!!! EXCEPCIÓN DETECTADA !!!")
        traceback.print_exc()
        
if __name__ == "__main__":
    simular_jornada()
