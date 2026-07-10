"""
Extensiones de Flask compartidas entre módulos.

Se instancian aquí (sin `app`) y se inicializan con `init_app` en la
factory (`app/__init__.py`), para evitar imports circulares entre las
rutas y la app.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
