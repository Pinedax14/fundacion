import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar conexión desde la nueva ubicación
from app.rutas.conexion import Conexion

# Importar función que registra todas las rutas
from app.rutas import registrar_todas_las_rutas

# Crear aplicación Flask
app = Flask(__name__,
           template_folder='app/templates',
           static_folder='app/static')

# Inicializar conexión a BD
conexion = Conexion(app)

# Registrar todas las rutas de la aplicación
registrar_todas_las_rutas(app, conexion)

if __name__ == '__main__':
    print("=" * 50)
    print("ALMAS CON COLA - Sistema de Gestión")
    print("=" * 50)
    print("Iniciando servidor en http://0.0.0.0:5000")
    print("=" * 50)

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )

