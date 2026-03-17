"""
Módulo de rutas para gestión de idioma
Contiene la funcionalidad para cambiar el idioma de la aplicación
"""

from flask import session, redirect, request, url_for


class RutasIdioma:
    """
    Gestiona el cambio de idioma de la aplicación:
    - Cambiar idioma (/cambiar_idioma/<lang>)
    Soporta español (es) e inglés (en)
    """

    def __init__(self, app, conexion):
        """
        Inicializa el gestor de idioma

        Args:
            app: Instancia de Flask
            conexion: Instancia de Conexion
        """
        self.app = app
        self.conexion = conexion
        self._registrar_rutas()

    def _registrar_rutas(self):
        """Registra las rutas de cambio de idioma"""
        self.app.add_url_rule('/cambiar_idioma/<lang>', 'cambiar_idioma',
                             self.cambiar_idioma, methods=['GET'])

    def cambiar_idioma(self, lang):
        """
        Cambia el idioma de la sesión del usuario

        Args:
            lang: Código de idioma ('es' para español, 'en' para inglés)
        """
        # Validar que el idioma sea soportado
        if lang in ['es', 'en']:
            session['language'] = lang

        # Redirigir a la página anterior (o a home si no hay referencia)
        return redirect(request.referrer or url_for('home'))
