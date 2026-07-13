import os
import re

# 1. Update db/conexion.py
with open('db/conexion.py', 'r', encoding='utf-8') as f:
    conexion_text = f.read()

new_normalizar = '''def normalizar_texto_busqueda(valor) -> str:
    if valor is None:
        return ""
    texto = str(valor).strip().casefold()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return ' '.join(texto.split())

def coincide_busqueda(texto_busqueda: str, campos: list) -> bool:
    """
    Estrategia centralizada de búsqueda en memoria.
    Verifica que todos los términos de la búsqueda existan en alguno de los campos.
    """
    texto = normalizar_texto_busqueda(texto_busqueda)
    if not texto:
        return True
    
    texto_campos = " ".join([normalizar_texto_busqueda(c) for c in campos if c is not None])
    
    for termino in texto.split():
        if termino not in texto_campos:
            return False
    return True'''

conexion_text = re.sub(
    r'def normalizar_texto_busqueda\(valor\) -> str:.*?(?=\ndef obtener_conexion\(\):)',
    new_normalizar + '\n\n',
    conexion_text,
    flags=re.DOTALL
)

with open('db/conexion.py', 'w', encoding='utf-8') as f:
    f.write(conexion_text)


# 2. Update db/queries_clientes.py
with open('db/queries_clientes.py', 'r', encoding='utf-8') as f:
    queries_clientes = f.read()

old_busqueda_clientes = r'''    from db\.conexion import normalizar_texto_busqueda
    patron_normalizado = f"%\{normalizar_texto_busqueda\(filtro\)\}%"

    clausulas_where = \[
        "\(NORMALIZAR\(c\.nombre_completo\) LIKE \? OR NORMALIZAR\(c\.cuit_dni\) LIKE \? OR NORMALIZAR\(c\.telefono\) LIKE \? OR NORMALIZAR\(c\.email\) LIKE \? OR NORMALIZAR\(c\.ciudad\) LIKE \? OR NORMALIZAR\(c\.direccion\) LIKE \? OR NORMALIZAR\(c\.condicion_iva\) LIKE \? OR EXISTS \(SELECT 1 FROM notas_cliente n WHERE n\.id_cliente = c\.id_cliente AND NORMALIZAR\(n\.contenido\) LIKE \?\)\)"
    \]
    params = \[patron_normalizado\] \* 8'''

new_busqueda_clientes = '''    from db.conexion import normalizar_texto_busqueda
    busqueda_norm = normalizar_texto_busqueda(filtro)
    
    clausulas_where = []
    params = []
    
    if busqueda_norm:
        terminos = busqueda_norm.split()
        for term in terminos:
            patron = f"%{term}%"
            clausulas_where.append(
                "(NORMALIZAR(c.nombre_completo) LIKE ? OR NORMALIZAR(c.cuit_dni) LIKE ? OR NORMALIZAR(c.telefono) LIKE ? OR NORMALIZAR(c.email) LIKE ? OR NORMALIZAR(c.ciudad) LIKE ? OR NORMALIZAR(c.direccion) LIKE ? OR NORMALIZAR(c.condicion_iva) LIKE ? OR EXISTS (SELECT 1 FROM notas_cliente n WHERE n.id_cliente = c.id_cliente AND NORMALIZAR(n.contenido) LIKE ?))"
            )
            params.extend([patron] * 8)
    else:
        # Dummy condition if no search text
        clausulas_where.append("1=1")'''

queries_clientes = re.sub(old_busqueda_clientes, new_busqueda_clientes, queries_clientes)

with open('db/queries_clientes.py', 'w', encoding='utf-8') as f:
    f.write(queries_clientes)


# 3. Update ui/modules/stock/tab_stock.py
with open('ui/modules/stock/tab_stock.py', 'r', encoding='utf-8') as f:
    stock_text = f.read()

old_stock_busqueda = r'''        texto = self\.input_buscar\.text\(\)\.strip\(\)\.lower\(\)
        idx_estado = self\.combo_estado\.currentIndex\(\)
        unidad_filtro = self\.combo_unidad\.currentData\(\)
        idx_orden = self\.combo_orden\.currentIndex\(\)

        datos_filtrados = \[\]
        for p in self\.datos_catalogo:
            if texto and texto not in p\[\"descripcion\"\]\.lower\(\) and texto not in p\[\"codigo\"\]\.lower\(\):
                continue'''

new_stock_busqueda = '''        from db.conexion import coincide_busqueda
        texto = self.input_buscar.text()
        idx_estado = self.combo_estado.currentIndex()
        unidad_filtro = self.combo_unidad.currentData()
        idx_orden = self.combo_orden.currentIndex()

        datos_filtrados = []
        for p in self.datos_catalogo:
            if not coincide_busqueda(texto, [p["codigo"], p["descripcion"], p.get("unidad_base", "")]):
                continue'''

stock_text = re.sub(old_stock_busqueda, new_stock_busqueda, stock_text)

with open('ui/modules/stock/tab_stock.py', 'w', encoding='utf-8') as f:
    f.write(stock_text)


# 4. Update ui/modules/ventas/tab_ventas.py
with open('ui/modules/ventas/tab_ventas.py', 'r', encoding='utf-8') as f:
    ventas_text = f.read()

old_ventas_busqueda = r'''    def filtrar_productos\(self, texto: str\) -> list\[dict\]:
        texto = texto\.strip\(\)\.lower\(\)
        if not texto:
            return \[\]
            
        exactos = \[\]
        empiezan_cod = \[\]
        empiezan_desc = \[\]
        contienen = \[\]
        
        for p in self\.catalogo:
            cod_low = p\['codigo'\]\.lower\(\)
            desc_low = p\['desc'\]\.lower\(\)
            
            if cod_low == texto:
                exactos\.append\(p\)
            elif cod_low\.startswith\(texto\):
                empiezan_cod\.append\(p\)
            elif desc_low\.startswith\(texto\):
                empiezan_desc\.append\(p\)
            elif texto in cod_low or texto in desc_low:
                contienen\.append\(p\)
                
        return exactos \+ empiezan_cod \+ empiezan_desc \+ contienen'''

new_ventas_busqueda = '''    def filtrar_productos(self, texto: str) -> list[dict]:
        from db.conexion import normalizar_texto_busqueda, coincide_busqueda
        texto_busqueda = texto
        texto_norm = normalizar_texto_busqueda(texto)
        if not texto_norm:
            return []
            
        exactos = []
        empiezan_cod = []
        empiezan_desc = []
        contienen = []
        
        for p in self.catalogo:
            cod_norm = normalizar_texto_busqueda(p['codigo'])
            desc_norm = normalizar_texto_busqueda(p['desc'])
            
            if not coincide_busqueda(texto_busqueda, [p['codigo'], p['desc']]):
                continue
                
            if cod_norm == texto_norm:
                exactos.append(p)
            elif cod_norm.startswith(texto_norm):
                empiezan_cod.append(p)
            elif desc_norm.startswith(texto_norm):
                empiezan_desc.append(p)
            else:
                contienen.append(p)
                
        return exactos + empiezan_cod + empiezan_desc + contienen'''

ventas_text = re.sub(old_ventas_busqueda, new_ventas_busqueda, ventas_text)

with open('ui/modules/ventas/tab_ventas.py', 'w', encoding='utf-8') as f:
    f.write(ventas_text)

print("Actualizaciones completadas")
