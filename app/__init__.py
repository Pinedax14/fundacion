"""
Factory pattern para crear la aplicación Flask
Permite crear instancias con diferentes configuraciones
"""

import os
from flask import Flask
from config import config_by_name
from app.models import db
from app.logger import setup_logger


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
    
    # Setup logging
    setup_logger(app)
    
    # Log de inicialización
    app.logger.info(f"Aplicación creada con config: {config_name}")
    app.logger.info(f"Debug: {app.debug}")
    app.logger.info(f"Testing: {app.testing}")
    
    # Registro de blueprints
    _register_blueprints(app)
    
    # Contexto de aplicación para migraciones
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        app.logger.info("Tablas de BD verificadas/creadas")
    
    return app, db


def _register_blueprints(app):
    """
    Registra todos los blueprints de la aplicación
    """
    try:
        # Blueprint de Auditoría (seguridad)
        from app.rutas.auditoria import auditoria_bp
        app.register_blueprint(auditoria_bp)
        app.logger.info("Blueprint auditoría registrado")
    except Exception as e:
        app.logger.warning(f"Error registrando blueprint auditoría: {e}")
