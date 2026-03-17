"""
Módulo de decoradores para autenticación y autorización
Contiene decoradores reutilizables para proteger rutas
"""

from functools import wraps
from flask import session, redirect, url_for, flash


def admin_required_factory(app):
    """
    Factory que crea un decorador para verificar si el usuario es administrador.
    Verifica que el usuario esté logueado y tenga rol de 'admin'.

    Retorna una función decoradora que valida credenciales de admin.
    Si no es admin, redirige a home y muestra un mensaje de error.
    """
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar si el usuario está logueado y tiene rol admin
            if 'loggedin' not in session or session.get('rol') != 'admin':
                flash('Acceso no autorizado. Debes ser administrador.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return admin_required
