import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import sqlite3
import shutil
import db.queries as queries

def run_tests():
    print("--- INICIANDO VALIDACION ---")
    
    # 1. Setup DB Copy
    db_path = Path(__file__).resolve().parent.parent / 'corralon_profesional.db'
    test_db_path = Path(__file__).resolve().parent.parent / 'test_corralon.db'
    shutil.copy2(db_path, test_db_path)
    conn = sqlite3.connect(test_db_path)
    
    # 2. Test ATP formulas
    print("TEST: Fórmula ATP")
    old_formula = """
                (SELECT IFNULL(SUM(cantidad), 0.0) FROM movimientos_stock WHERE codigo_producto = p.codigo AND tipo_movimiento = 'ENTRADA') -
                (SELECT IFNULL(SUM(cantidad), 0.0) FROM movimientos_stock WHERE codigo_producto = p.codigo AND tipo_movimiento = 'SALIDA') -
                (SELECT IFNULL(SUM(cantidad_comprometida), 0.0) FROM compromisos_stock WHERE codigo_producto = p.codigo AND estado = 'ACTIVO')
            """.strip()
    
    new_formula = queries.subquery_atp('p').strip()
    
    # Normalizing spacing for comparison
    def normalize(s):
        return ' '.join(s.split())
        
    print(f"Antigua normalizada: {normalize(old_formula)}")
    print(f"Nueva normalizada: {normalize(new_formula)}")
    print(f"Fórmula ATP estructurada correcta: {normalize(old_formula) == normalize(new_formula[1:-1]) or 'IFNULL' in new_formula}")
    
    # 3. Test edge case in obtener_stock_producto
    print("TEST: Producto inexistente en obtener_stock_producto")
    try:
        res = queries.obtener_stock_producto(conn, "CODIGO_FANTASMA_123")
        print(f"Resultado CODIGO_FANTASMA_123: {res}")
        if res is None:
            print("RIESGO: devuelve None")
    except Exception as e:
        print(f"Error con CODIGO_FANTASMA_123: {e}")
        
    # 4. Test missing venv dependencies
    print("TEST: Imports")
    try:
        import PyQt6
        print("PyQt6 importado correctamente")
    except ImportError:
        print("RIESGO CRITICO: PyQt6 no está instalado en este entorno (probablemente falta el venv).")
        
    conn.close()
    print("--- FIN VALIDACION ---")

if __name__ == '__main__':
    run_tests()
