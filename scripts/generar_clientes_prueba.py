import sqlite3
import random
import os

# Datos para combinaciones
NOMBRES = ["Juan", "María", "Carlos", "Ana", "Luis", "Elena", "Diego", "Sofía", "Martín", "Lucía",
           "Maximiliano", "Guillermina", "Héctor", "Mónica", "Raúl", "Valeria", "Jorge", "Carolina",
           "Federico", "Florencia", "Agustín", "Camila", "Joaquín", "Micaela", "Tomás", "Martina"]
APELLIDOS = ["Gómez", "Rodríguez", "López", "Fernández", "Pérez", "González", "Sánchez", "Romero",
             "Sosa", "Torres", "Álvarez", "Díaz", "Ruiz", "Ramírez", "Flores", "Benítez", "Acosta",
             "Medina", "Herrera", "Aguilar", "Rojas", "García", "Molina", "Silva", "Ortiz", "Luna"]
EMPRESAS = ["Construcciones", "Desarrollos", "Ingeniería", "Arquitectura", "Servicios",
            "Materiales", "Logística", "Obras", "Proyectos", "Instalaciones"]
EMPRESAS_SUFIJOS = ["S.A.", "S.R.L.", "S.A.S.", "y Asociados", "Hnos."]

CIUDADES = ["Córdoba", "Buenos Aires", "Rosario", "Mendoza", "Tucumán", "La Plata", "Mar del Plata",
            "Salta", "Santa Fe", "San Juan", "Resistencia", "Neuquén", "Posadas", "Formosa", "Jujuy",
            "San Luis", "Paraná", "Corrientes", "Bahía Blanca", "Villa María", "Río Cuarto", "San Rafael",
            "Bariloche", "Viedma", "Trelew", "Comodoro Rivadavia", "Río Gallegos", "Ushuaia",
            "San Miguel de Tucumán", "San Salvador de Jujuy", "Santiago del Estero", "Santa Rosa"]

CALLES = ["San Martín", "Belgrano", "Sarmiento", "Mitre", "Rivadavia", "Moreno", "Urquiza", "Alberdi",
          "Av. de Mayo", "Av. 9 de Julio", "Av. Corrientes", "Av. Callao", "Av. Santa Fe", "Av. Córdoba",
          "Av. Libertador", "Av. Figueroa Alcorta", "Av. Pueyrredón", "Av. Las Heras", "Av. Alvear",
          "Av. de los Incas", "Av. Triunvirato", "Av. Monroe", "Av. Cabildo", "Av. Juramento"]

def generar_cuit_dni(es_empresa: bool) -> str:
    if es_empresa:
        prefijo = random.choice(["30", "33", "34"])
        cuerpo = f"{random.randint(50000000, 79999999)}"
        sufijo = random.randint(0, 9)
        return f"{prefijo}-{cuerpo}-{sufijo}"
    else:
        prefijo = random.choice(["20", "23", "24", "27"])
        cuerpo = f"{random.randint(10000000, 45999999)}"
        sufijo = random.randint(0, 9)
        return f"{prefijo}-{cuerpo}-{sufijo}"

def generar_telefono() -> str:
    if random.random() < 0.15:
        return ""
    fmt = random.choice([
        "351 {num}", "0351-{num}", "11 {num}", "351{num}", "+549351{num}"
    ])
    num = random.randint(2000000, 9999999)
    return fmt.format(num=num)

def generar_email(nombre: str) -> str:
    if random.random() < 0.2:
        return ""
    import unicodedata
    base = nombre.lower().replace(" ", ".").strip()
    base = ''.join(c for c in unicodedata.normalize('NFD', base) if unicodedata.category(c) != 'Mn')
    base = "".join([c for c in base if c.isalnum() or c == "."])
    dominios = ["gmail.com", "hotmail.com", "yahoo.com.ar", "outlook.com", "empresa.com.ar", "constructora.net"]
    return f"{base}@{random.choice(dominios)}"

def generar_direccion() -> str:
    if random.random() < 0.1:
        return ""
    calle = random.choice(CALLES)
    num = random.randint(100, 9999)
    if random.random() < 0.2:
        return f"{calle} {num} - Piso {random.randint(1,10)} Depto {random.choice(['A','B','C','D'])} - Complejo habitacional Zona Norte Mz {random.randint(1,10)} Lote {random.randint(1,20)}"
    return f"{calle} {num}"

def run():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'corralon_profesional.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    num_clientes = random.randint(70, 90)
    
    insertados = 0
    for _ in range(num_clientes):
        es_empresa = random.random() < 0.3
        
        if es_empresa:
            apellido = random.choice(APELLIDOS)
            emp = random.choice(EMPRESAS)
            suf = random.choice(EMPRESAS_SUFIJOS)
            if random.random() < 0.1:
                nombre_base = f"{apellido} {emp} Constructora e Inmobiliaria {suf}"
            else:
                nombre_base = f"{apellido} {emp} {suf}"
        else:
            n1 = random.choice(NOMBRES)
            a1 = random.choice(APELLIDOS)
            if random.random() < 0.3:
                n2 = random.choice(NOMBRES)
                a2 = random.choice(APELLIDOS)
                nombre_base = f"{n1} {n2} {a1} {a2}"
            else:
                nombre_base = f"{n1} {a1}"
                
            if random.random() < 0.05:
                nombre_base += " y familiares encargados de la obra en el interior de la provincia"

        # IDENTIFICADOR SEGURO
        nombre_completo = f"[TEST] {nombre_base}"
        
        cuit = generar_cuit_dni(es_empresa)
        if random.random() < 0.1:
            cuit = None
            
        tel = generar_telefono()
        email = generar_email(nombre_base)
        
        ciudad = random.choice(CIUDADES)
        if random.random() < 0.1:
            ciudad = ""
            
        direccion = generar_direccion()
        
        if es_empresa:
            condicion = random.choice(["Responsable Inscripto", "Exento"])
        else:
            condicion = random.choice(["Consumidor Final", "Monotributista"])
            
        activo = 1 if random.random() < 0.9 else 0
        
        c.execute('''
            INSERT INTO clientes (nombre_completo, cuit_dni, telefono, email, activo, ciudad, direccion, condicion_iva)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nombre_completo, cuit, tel, email, activo, ciudad, direccion, condicion))
        insertados += 1
        
    conn.commit()
    conn.close()
    
    print(f"ÉXITO: Se insertaron {insertados} clientes ficticios.")
    print("Para eliminarlos, ejecute: DELETE FROM clientes WHERE nombre_completo LIKE '[TEST] %';")

if __name__ == '__main__':
    run()
