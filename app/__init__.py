"""
Factory pattern para crear la aplicación Flask
Permite crear instancias con diferentes configuraciones
"""

import os
from flask import Flask, flash, redirect, request
from config import config_by_name
from app.models import db
from app.logger import setup_logger
from app.extensions import limiter


def create_app(config_name=None):
    """
    Factory function para crear la aplicación Flask
    
    Args:
        config_name (str): Nombre de la configuración ('development', 'testing', 'production')
        Si no se proporciona, usa la del archivo .env o 'development' por default
    
    Returns:
        tuple: (app, db) - Flask app instance y SQLAlchemy db instance
    """
    
    # Determinar configuración
    if not config_name:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config_class = config_by_name.get(config_name, config_by_name['default'])
    
    # Obtener ruta absoluta del directorio de la app
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Crear aplicación con rutas absolutas
    app = Flask(
        __name__,
        template_folder=os.path.join(app_dir, 'templates'),
        static_folder=os.path.join(app_dir, 'static')
    )
    
    # Cargar configuración
    app.config.from_object(config_class)
    
    # Inicializar extensiones
    db.init_app(app)
    limiter.init_app(app)
    
    # Setup logging
    setup_logger(app)
    
    # Log de inicialización
    app.logger.info(f"Aplicación creada con config: {config_name}")
    app.logger.info(f"Debug: {app.debug}")
    app.logger.info(f"Testing: {app.testing}")

    # Registrar rutas y blueprints
    from app.rutas import registrar_todas_las_rutas
    from app.rutas.conexion import Conexion

    conexion = Conexion(app)
    registrar_todas_las_rutas(app, conexion)

    @app.errorhandler(429)
    def demasiados_intentos(e):
        """Respuesta amigable cuando Flask-Limiter bloquea por exceso de intentos.

        Se redirige (302) en vez de devolver el 429 crudo para que el navegador
        siga la redirección y el usuario vea el mensaje flash.
        """
        flash('Demasiados intentos. Espera un minuto antes de volver a intentarlo.', 'danger')
        return redirect(request.path)


    # Contexto de aplicación para migraciones
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        app.logger.info("Tablas de BD verificadas/creadas")
    
    return app, db
