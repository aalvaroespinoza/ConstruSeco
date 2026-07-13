import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.theme import aplicar_tema_claro
# Importamos la base de datos y tu pestaña recién creada
from db.conexion import obtener_conexion, inicializar_base_datos, limpiar_presupuestos_vencidos
from ui.ventana_principal import VentanaPrincipal


if __name__ == "__main__":
    # Primero nos aseguramos de que las tablas existan en la base de datos
    inicializar_base_datos()
    
    # Levantamos la interfaz gráfica
    app = QApplication(sys.argv)
    aplicar_tema_claro(app)

    # Ruta robusta al logo, independiente del directorio de ejecución
    _BASE_DIR = Path(__file__).resolve().parent
    _icono = QIcon(str(_BASE_DIR / "assets" / "logo.png"))
    app.setWindowIcon(_icono)

    conexion = obtener_conexion()

    # Liberar compromisos de presupuestos vencidos antes de mostrar datos.
    # El error se captura para que un fallo secundario nunca bloquee el arranque.
    try:
        limpiar_presupuestos_vencidos(conexion)
    except Exception as _atp_err:
        print(f"[AVISO] No se pudieron liberar presupuestos vencidos: {_atp_err}")

    ventana = VentanaPrincipal(conexion)
    ventana.setWindowIcon(_icono)   # refuerzo en la QMainWindow
    ventana.show()
    sys.exit(app.exec())
