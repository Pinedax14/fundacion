import os

import sys
sys.path.insert(0, os.path.dirname(__file__))
from flask import Flask
from app.conexion import Conexion
from sqlalchemy import text


# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

print("=" * 50)
print("🧪 INICIANDO PRUEBA DE CONEXIÓN A POSTGRESQL")
print("=" * 50)

# 1. Crear una app Flask de prueba
app = Flask(__name__)

# 2. Inicializar la conexión (debería detectar DATABASE_URL)
conexion = Conexion(app)

# 3. Intentar una consulta simple
try:
    print("📡 Conectando a la base de datos...")
    
    with app.app_context():
        # Consultar cantidad de usuarios
        result = conexion.db.session.execute(text("SELECT COUNT(*) as total FROM usuarios"))
        total_usuarios = result.fetchone()[0]
        
        print(f"✅ CONEXIÓN EXITOSA")
        print(f"   Total de usuarios en la BD: {total_usuarios}")
        
        # Consultar los primeros 2 usuarios
        result = conexion.db.session.execute(text("SELECT id, nombre, email FROM usuarios LIMIT 2"))
        usuarios = result.fetchall()
        
        print(f"   Primeros 2 usuarios:")
        for usuario in usuarios:
            print(f"   - ID: {usuario.id}, Nombre: {usuario.nombre}")
            
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}")
    print(f"   Mensaje: {e}")
    print("   Verifica tu variable DATABASE_URL en el archivo .env")

print("=" * 50)
print("Prueba finalizada.")
print("=" * 50)