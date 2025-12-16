# app/rutas_pdf.py
from flask import send_file, flash, redirect, url_for, session
from functools import wraps
from app.reportes import PDFGenerator

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session or session.get('rol') != 'admin':
            flash('Acceso denegado. Solo administradores pueden generar reportes.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class RutasPDF:
    def __init__(self, app, conexion):
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
    
    @admin_required
    def reporte_usuarios(self):
        """Genera reporte PDF de usuarios"""
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
    
    @admin_required
    def reporte_mascotas(self):
        """Genera reporte PDF de mascotas"""
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
    
    @admin_required
    def reporte_donaciones(self):
        """Genera reporte PDF de donaciones"""
        try:
            cursor = self.conexion.mysql.connection.cursor()
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
    
    @admin_required
    def reporte_maltrato(self):
        """Genera reporte PDF de reportes de maltrato"""
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
        """Retorna la fecha actual en formato YYYYMMDD"""
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d')


class RutasIdioma:
    """Gestiona el cambio de idioma"""
    
    def __init__(self, app, conexion):
        self.app = app
        self.conexion = conexion
        self._registrar_rutas()
    
    def _registrar_rutas(self):
        """Registra las rutas de idioma"""
        self.app.add_url_rule('/cambiar_idioma/<lang>', 'cambiar_idioma', 
                             self.cambiar_idioma, methods=['GET'])
    
    def cambiar_idioma(self, lang):
        """Cambia el idioma de la aplicación"""
        from flask import session, redirect, request
        
        # Validar que el idioma sea válido
        if lang in ['es', 'en']:
            session['language'] = lang
        
        # Redirigir a la página anterior
        return redirect(request.referrer or url_for('home'))