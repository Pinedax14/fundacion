"""
Servicios de usuario que usan procedimientos almacenados PostgreSQL/Neon
"""

from sqlalchemy import text
from app.models import db
from app.utils.data_structures import LinkedList


class PostgresUserService:
    """Servicio para registrar usuarios y trabajar con usuarios en memoria."""

    def registrar_usuario(self, nombre, email, password_hash, fecha_nacimiento=None):
        """Registra un usuario usando un procedimiento almacenado en PostgreSQL.

        El procedimiento esperado en Neon es:

            CREATE OR REPLACE FUNCTION sp_registrar_usuario(
                p_nombre TEXT,
                p_email TEXT,
                p_password TEXT,
                p_fecha_nacimiento DATE
            ) RETURNS INTEGER LANGUAGE plpgsql AS $$
            DECLARE
                v_id INTEGER;
            BEGIN
                INSERT INTO usuarios(nombre, email, password, fecha_nacimiento, rol, verified, fecha_registro)
                VALUES (p_nombre, p_email, p_password, p_fecha_nacimiento, 'user', false, NOW())
                RETURNING id INTO v_id;
                RETURN v_id;
            END;
            $$;

        Args:
            nombre (str): nombre completo del usuario.
            email (str): correo electrónico único.
            password_hash (str): contraseña hasheada.
            fecha_nacimiento (date | None): fecha de nacimiento.

        Returns:
            int | None: id del usuario registrado, o None en caso de error.
        """
        try:
            sql = text(
                "SELECT sp_registrar_usuario(:nombre, :email, :password, :fecha_nacimiento) AS usuario_id"
            )
            result = db.session.execute(sql, {
                'nombre': nombre,
                'email': email,
                'password': password_hash,
                'fecha_nacimiento': fecha_nacimiento
            })
            usuario_id = result.scalar()
            db.session.commit()
            return usuario_id
        except Exception as e:
            db.session.rollback()
            raise

    def obtener_usuario_por_email(self, email):
        """Obtiene un usuario por email usando SQL directo, sin ORM."""
        sql = text("SELECT id, nombre, email, fecha_nacimiento, rol, verified FROM usuarios WHERE email = :email")
        result = db.session.execute(sql, {'email': email}).mappings().first()
        return dict(result) if result else None

    def listar_usuarios_en_linkedlist(self):
        """Carga todos los usuarios en una lista enlazada para procesamiento en memoria."""
        sql = text(
            "SELECT id, nombre, email, fecha_nacimiento, rol, verified, fecha_registro "
            "FROM usuarios ORDER BY fecha_registro DESC"
        )
        result = db.session.execute(sql).mappings().all()
        lista = LinkedList()
        for row in result:
            lista.append(dict(row))
        return lista

    def buscar_usuario_en_linkedlist(self, usuarios_linkedlist, email):
        """Busca un usuario en la lista enlazada por email."""
        return usuarios_linkedlist.find(lambda usuario: usuario.get('email') == email)
