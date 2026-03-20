"""
Módulo legado para compatibilidad con rutas antiguas.

En el nuevo refactor:
- Usar app.models.db para ORM
- Usar app.services para lógica de negocio
- Usar app.validators para validación

Esta clase solo existe para mantener las rutas antiguas funcionando.
"""

from flask_bcrypt import Bcrypt
import os
from app.models import db


class RowObject:
    """Objeto que permite acceder a datos como atributos (compatible con Jinja2)"""
    def __init__(self, data):
        self.__dict__.update(data)
    
    def __getitem__(self, key):
        return self.__dict__.get(key)
    
    def get(self, key, default=None):
        return self.__dict__.get(key, default)
    
    def __repr__(self):
        return f"RowObject({self.__dict__})"


class LegacyCursor:
    """
    Proxy que simula un cursor SQL ejecutable.
    Convierte queries SQL directas a ORM cuando es posible.
    """
    def __init__(self, db):
        self.db = db
        self.result = None
    
    def execute(self, query, params=None):
        """Ejecuta una query SQL usando SQLAlchemy raw SQL"""
        try:
            from sqlalchemy import text, bindparam
            
            if not params:
                # Sin parámetros
                result = self.db.session.execute(text(query))
            else:
                # Con parámetros - usar bindparams para compatibilidad
                # Convertir %s a :param_0, :param_1, etc
                import re
                
                if isinstance(params, (list, tuple)):
                    # Crear parámetros nombrados
                    query_with_params = query
                    param_dict = {}
                    
                    # Reemplazar cada %s con :param_i
                    for i, param in enumerate(params):
                        query_with_params = query_with_params.replace('%s', f':param_{i}', 1)
                        param_dict[f'param_{i}'] = param
                    
                    result = self.db.session.execute(text(query_with_params), param_dict)
                else:
                    # Ya es un diccionario
                    result = self.db.session.execute(text(query), params)
            
            self.result = result
            # Para INSERT/UPDATE/DELETE, no mantener el result ya que se cierra automáticamente,
            # excepto si tienen RETURNING
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')) and 'RETURNING' not in query.upper():
                self.result = None
            return self
        except Exception as e:
            print(f"Error en query: {str(e)}")
            raise
    
    def fetchone(self):
        """Devuelve un registro como objeto accesible"""
        if self.result:
            row = self.result.fetchone()
            if row:
                # Convertir a objeto accesible por atributos
                return self._row_to_object(row)
            return None
        return None
    
    def fetchall(self):
        """Devuelve todos los registros como objetos accesibles"""
        if self.result:
            rows = self.result.fetchall()
            result = []
            for row in rows:
                result.append(self._row_to_object(row))
            return result
        return []
    
    def close(self):
        """Cierra el cursor (compatibilidad con interfaz legada)"""
        pass  # SQLAlchemy gestiona esto automáticamente
    
    def _row_to_object(self, row):
        """Convierte una Row a un objeto accesible por atributos (para Jinja2)"""
        if isinstance(row, dict):
            # Ya es diccionario
            return RowObject(row)
        elif hasattr(row, '_mapping'):
            # Es un SQLAlchemy Row object
            return RowObject(dict(row._mapping))
        elif isinstance(row, (list, tuple)):
            # Es una tupla/lista - convertir a diccionario basado en posición
            # Esto es un fallback, idealmente no debería ocurrir
            return row
        else:
            return row


class Conexion:
    """
    Clase legado para compatibilidad con rutas antiguas (legacy support).
    Proporciona interfaz similar a la versión anterior usando el nuevo ORM.
    """
    def __init__(self, app):
        self.app = app
        self.db = db
        
        # Seguridad
        if not app.config.get('SECRET_KEY') or app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            app.secret_key = os.urandom(32)
        
        # Uploads
        app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images', 'reportes')
        app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
        app.config['UPLOAD_FOLDER_PERFILES'] = os.path.join('static', 'uploads', 'perfiles')
        app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
        
        # Bcrypt
        self.bcrypt = Bcrypt(app)
        
        # MySQL compatibility - devuelve proxy de la conexión
        self._mysql_proxy = None
        
        print("=" * 50)
        print("Conexión legado inicializada (compatibilidad)")
        print("=" * 50)
    
    @property
    def mysql(self):
        """Propiedad para compatibilidad con rutas que esperan conexión MySQL"""
        if self._mysql_proxy is None:
            # Crear proxy que devuelve cursores
            class MySQLProxy:
                def __init__(self, conexion):
                    self.conexion = conexion
                
                @property
                def connection(self):
                    # Devolver conexión raw
                    return self.conexion.db.engine.raw_connection()
                
                def cursor(self, cursor_class=None):
                    # Devolver un LegacyCursor
                    return self.conexion.get_cursor()
            
            self._mysql_proxy = MySQLProxy(self)
        
        return self._mysql_proxy
    
    def get_cursor(self):
        """Devuelve un cursor simulado para compatibilidad"""
        return LegacyCursor(self.db)
    
    def commit(self):
        """Realiza commit"""
        self.db.session.commit()
    
    def rollback(self):
        """Realiza rollback"""
        self.db.session.rollback()
    
    def allowed_file(self, filename):
        """Verifica extensión permitida"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.app.config['ALLOWED_EXTENSIONS']
