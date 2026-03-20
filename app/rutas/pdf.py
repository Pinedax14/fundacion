"""
Módulo de rutas para generación de reportes PDF
Contiene las rutas para generar diferentes tipos de reportes
Requiere rol de administrador
"""

from datetime import datetime
from flask import send_file, flash, redirect, url_for, session
from functools import wraps
from app.rutas.pdf_generator import PDFGenerator


def admin_required_decorator(f):
    """
    Decorador que verifica si el usuario es administrador
    Usado internamente en las rutas PDF
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session or session.get('rol') != 'admin':
            flash('Acceso denegado. Solo administradores pueden generar reportes.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


class RutasPDF:
    """
    Gestiona la generación de reportes PDF:
    - Reporte de usuarios (/reporte/usuarios)
    - Reporte de mascotas (/reporte/mascotas)
    - Reporte de donaciones (/reporte/donaciones)
    - Reporte de maltrato (/reporte/maltrato)
    """

    def __init__(self, app, conexion):
        """
        Inicializa el generador de reportes PDF

        Args:
            app: Instancia de Flask
            conexion: Instancia de Conexion
        """
        self.app = app
        self.conexion = conexion
        self.pdf_gen = PDFGenerator()
        self._registrar_rutas()

    def _registrar_rutas(self):
        """Registra todas las rutas de reportes PDF"""
        self.app.add_url_rule('/reporte/usuarios', 'reporte_usuarios',
                             self.reporte_usuarios, methods=['GET'])
        self.app.add_url_rule('/reporte/mascotas', 'reporte_mascotas',
                             self.reporte_mascotas, methods=['GET'])
        self.app.add_url_rule('/reporte/donaciones', 'reporte_donaciones',
                             self.reporte_donaciones, methods=['GET'])
        self.app.add_url_rule('/reporte/maltrato', 'reporte_maltrato',
                             self.reporte_maltrato, methods=['GET'])

    @admin_required_decorator
    def reporte_usuarios(self):
        """
        Genera un reporte PDF con la lista de usuarios registrados
        Solo accessibles por administradores
        """
        try:
            cursor = self.conexion.mysql.connection.cursor()
            cursor.execute("SELECT id, nombre, email, password, fecha_registro, rol FROM usuarios ORDER BY fecha_registro DESC")
            usuarios = cursor.fetchall()
            cursor.close()

            if not usuarios:
                flash("No hay usuarios registrados para generar el reporte", "warning")
                return redirect(url_for('admin_panel'))

            buffer = self.pdf_gen.generar_reporte_usuarios(usuarios)

            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"reporte_usuarios_{self._fecha_hoy()}.pdf",
                mimetype='application/pdf'
            )
        except Exception as e:
            print(f"Error al generar reporte de usuarios: {e}")
            flash("Error al generar el reporte PDF", "danger")
            return redirect(url_for('admin_panel'))

    @admin_required_decorator
    def reporte_mascotas(self):
        """
        Genera un reporte PDF con la lista de mascotas en el sistema
        Solo accessibles por administradores
        """
        try:
            cursor = self.conexion.mysql.connection.cursor()
            cursor.execute("""
                SELECT id, nombre, especie, raza, edad, sexo, descripcion,
                       foto_url, estado, fecha_ingreso
                FROM mascotas
                ORDER BY fecha_ingreso DESC
            """)
            mascotas = cursor.fetchall()
            cursor.close()

            if not mascotas:
                flash("No hay mascotas registradas para generar el reporte", "warning")
                return redirect(url_for('admin_panel'))

            buffer = self.pdf_gen.generar_reporte_mascotas(mascotas)

            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"reporte_mascotas_{self._fecha_hoy()}.pdf",
                mimetype='application/pdf'
            )
        except Exception as e:
            print(f"Error al generar reporte de mascotas: {e}")
            flash("Error al generar el reporte PDF", "danger")
            return redirect(url_for('admin_panel'))

    @admin_required_decorator
    def reporte_donaciones(self):
        """
        Genera un reporte PDF con la lista de donaciones
        Solo accessibles por administradores
        """
        try:
            cursor = self.conexion.get_cursor()
            cursor.execute("""
                SELECT id, nombre_donante, contacto_email, tipo_donacion,
                       descripcion_donacion, fecha_donacion, estado_entrega
                FROM donaciones_items
                ORDER BY fecha_donacion DESC
            """)
            donaciones = cursor.fetchall()
            cursor.close()

            if not donaciones:
                flash("No hay donaciones registradas para generar el reporte", "warning")
                return redirect(url_for('admin_panel'))

            buffer = self.pdf_gen.generar_reporte_donaciones(donaciones)

            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"reporte_donaciones_{self._fecha_hoy()}.pdf",
                mimetype='application/pdf'
            )
        except Exception as e:
            print(f"Error al generar reporte de donaciones: {e}")
            flash("Error al generar el reporte PDF", "danger")
            return redirect(url_for('admin_panel'))

    @admin_required_decorator
    def reporte_maltrato(self):
        """
        Genera un reporte PDF con la lista de reportes de maltrato animal
        Solo accessibles por administradores
        """
        try:
            cursor = self.conexion.mysql.connection.cursor()
            cursor.execute("""
                SELECT id, ubicacion, descripcion_incidente, foto_evidencia_url,
                       fecha_reporte, estado_reporte
                FROM reportes
                ORDER BY fecha_reporte DESC
            """)
            reportes = cursor.fetchall()
            cursor.close()

            if not reportes:
                flash("No hay reportes de maltrato registrados", "warning")
                return redirect(url_for('admin_panel'))

            buffer = self.pdf_gen.generar_reporte_maltrato(reportes)

            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"reporte_maltrato_{self._fecha_hoy()}.pdf",
                mimetype='application/pdf'
            )
        except Exception as e:
            print(f"Error al generar reporte de maltrato: {e}")
            flash("Error al generar el reporte PDF", "danger")
            return redirect(url_for('admin_panel'))

    def _fecha_hoy(self):
        """
        Retorna la fecha actual en formato YYYYMMDD para el nombre del archivo
        """
        return datetime.now().strftime('%Y%m%d')
