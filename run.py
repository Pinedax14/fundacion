import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from app import create_app

# Cargar variables de entorno
load_dotenv()

# Crear aplicación con Factory Pattern
app, db = create_app()

# Importar rutas (mientras no hayan blueprints)
from app.rutas import registrar_todas_las_rutas
from app.rutas.conexion import Conexion

# Configurar conexión (legacy support)
conexion = Conexion(app)
registrar_todas_las_rutas(app, conexion)

if __name__ == '__main__':
    print("=" * 50)
    print("ALMAS CON COLA - Sistema de Gestión")
    print("=" * 50)
    print(f"Iniciando servidor en http://0.0.0.0:5000")
    print(f"Ambiente: {os.getenv('FLASK_ENV', 'development')}")
    print("=" * 50)

    app.run(
        debug=app.debug,
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 5000)),
        threaded=True
    )

