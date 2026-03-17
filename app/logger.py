"""
Configuración de logging centralizado
"""

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(app):
    """
    Configura el logging para la aplicación
    """
    
    # Crear carpeta de logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configurar nivel de log
    log_level = getattr(logging, app.config['LOG_LEVEL'], logging.INFO)
    
    # Handler para archivo
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s en %(name)s: %(message)s'
    ))
    file_handler.setLevel(log_level)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s'
    ))
    console_handler.setLevel(log_level)
    
    # Agregar handlers a la app
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    # Loguear que se inicializó
    app.logger.info('Logging configurado correctamente')
    app.logger.info(f'Nivel de log: {app.config["LOG_LEVEL"]}')
    app.logger.info(f'Base de datos: {app.config.get("SQLALCHEMY_DATABASE_URI", "No configurada")[:50]}...')
