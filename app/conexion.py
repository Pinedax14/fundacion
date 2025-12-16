from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
import psycopg2
from psycopg2.extras import DictCursor
from sqlalchemy import create_engine

class Conexion:
    def __init__(self, app):
        # Clave secreta
        app.secret_key = os.getenv('SECRET_KEY', 'clave_temporal_123')
        
        print("=" * 50)
        print(f"DB_HOST: {os.getenv('DB_HOST')}")
        print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
        
        # Configuración PostgreSQL (Neon) - PERO con fallback a MySQL
        database_url = os.getenv('DATABASE_URL')
        self.use_postgresql = False  # Valor por defecto
        
        if database_url:
            # Usar PostgreSQL (Neon)
            print("USANDO: PostgreSQL (Neon)")
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            self.db = SQLAlchemy(app)
            self.use_postgresql = True
        else:
            # Usar MySQL (local) como fallback
            print("USANDO: MySQL (local)")
            app.config['MYSQL_HOST'] = os.getenv('DB_HOST', 'localhost')
            app.config['MYSQL_USER'] = os.getenv('DB_USER', 'root')
            app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD', '')
            app.config['MYSQL_DB'] = os.getenv('DB_NAME', 'fundacion')
            app.config['MYSQL_AUTOCOMMIT'] = True
            from flask_mysqldb import MySQL
            self._mysql = MySQL(app)  # Cabiado a _mysql
            self.use_postgresql = False
        
        print("=" * 50)
        
        # Configuración de subida de imágenes (igual)
        app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images', 'reportes')
        app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
        app.config['UPLOAD_FOLDER_PERFILES'] = os.path.join('static', 'uploads', 'perfiles')
        app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB máximo
        
        self.bcrypt = Bcrypt(app)
    
    @property
    def mysql(self):
        """Propiedad para compatibilidad con código existente"""
        if hasattr(self, 'use_postgresql') and not self.use_postgresql:
            # MySQL mode
            return self._mysql
        else:
            # PostgreSQL mode - devolver objeto similar
            class PseudoMySQL:
                def __init__(self, conexion):
                    self.conexion = conexion
                
                @property
                def connection(self):
                    conn = self.conexion.db.engine.raw_connection()
                    return conn
                
                def cursor(self, cursor_class=None):
                    conn = self.connection
                    if cursor_class == DictCursor:
                        return conn.cursor(cursor_factory=DictCursor)
                    return conn.cursor()
            
            return PseudoMySQL(self)
    
    def get_cursor(self):
        """Obtiene cursor según el motor de base de datos"""
        if hasattr(self, 'use_postgresql') and self.use_postgresql:
            # PostgreSQL
            conn = self.db.engine.raw_connection()
            return conn.cursor(cursor_factory=DictCursor)
        else:
            # MySQL
            return self._mysql.connection.cursor()
    
    def commit(self):
        print("[DEBUG CONEXION] Método commit() llamado")
        """Commit según el motor"""
        if hasattr(self, 'use_postgresql') and self.use_postgresql:
            print("[DEBUG CONEXION] Usando PostgreSQL, llamando a self.db.session.commit()")
            connection = self.db.engine.raw_connection()
            connection.commit()
            connection.close()
        else:
            print("[DEBUG CONEXION] Usando MySQL, llamando a self._mysql.connection.commit")
            self._mysql.connection.commit()
    
    def allowed_file(self, filename, app):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']