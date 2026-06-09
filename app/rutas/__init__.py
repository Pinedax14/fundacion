"""
Paquete de rutas de la aplicación Almas con Cola
Importa todas las clases de rutas y las registra con la aplicación Flask
"""

from app.rutas.decoradores import admin_required_factory
from app.rutas.conexion import Conexion
from app.rutas.pdf_generator import PDFGenerator
from app.rutas.home import RutasHome
from app.rutas.auth import RutasAuth
from app.rutas.mascotas import RutasMascotas
from app.rutas.reportes import RutasReportes
from app.rutas.admin import RutasAdmin
from app.rutas.pdf import RutasPDF
from app.rutas.idioma import RutasIdioma
from app.rutas.auditoria import auditoria_bp


def registrar_todas_las_rutas(app, conexion):
    """
    Registra todas las rutas de la aplicación

    Esta función centraliza el registro de todos los manejadores de rutas.
    Se llama desde el archivo principal (run.py) o desde la fábrica de la aplicación.

    Args:
        app: Instancia de Flask
        conexion: Instancia de Conexion (conexión a base de datos)
    """
    # Registrar rutas públicas
    rutas_home = RutasHome(app, conexion)
    rutas_auth = RutasAuth(app, conexion)
    rutas_mascotas = RutasMascotas(app, conexion)
    rutas_reportes = RutasReportes(app, conexion)

    # Registrar rutas administrativas
    rutas_admin = RutasAdmin(app, conexion)

    # Registrar rutas de reportes PDF
    rutas_pdf = RutasPDF(app, conexion)

    # Registrar rutas de idioma
    rutas_idioma = RutasIdioma(app, conexion)

    # Registrar blueprint de auditoría
    app.register_blueprint(auditoria_bp)
    app.logger.info("Blueprint auditoría registrado")

    return {
        'home': rutas_home,
        'auth': rutas_auth,
        'mascotas': rutas_mascotas,
        'reportes': rutas_reportes,
        'admin': rutas_admin,
        'pdf': rutas_pdf,
        'idioma': rutas_idioma,
    }


__all__ = [
    'admin_required_factory',
    'Conexion',
    'PDFGenerator',
    'RutasHome',
    'RutasAuth',
    'RutasMascotas',
    'RutasReportes',
    'RutasAdmin',
    'RutasPDF',
    'RutasIdioma',
    'registrar_todas_las_rutas',
]
