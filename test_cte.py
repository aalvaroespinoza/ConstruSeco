import sqlite3
conn = sqlite3.connect('corralon_profesional.db')
c = conn.cursor()
c.execute('''
WITH CTE_Saldos AS (
    SELECT 
        m.*, 
        SUM(CASE WHEN m.tipo_movimiento = 'ENTRADA' THEN m.cantidad ELSE -m.cantidad END) 
        OVER (
            PARTITION BY m.codigo_producto 
            ORDER BY m.fecha_hora ASC, m.id_movimiento ASC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as stock_posterior 
    FROM movimientos_stock m
) 
SELECT * FROM CTE_Saldos LIMIT 5;
''')
print(c.fetchall())
