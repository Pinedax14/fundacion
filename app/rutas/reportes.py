"""
Módulo de rutas para reportes de maltrato animal
Contiene las rutas para crear y procesar reportes de maltrato
"""

from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os


class RutasReportes:
    """
    Gestiona rutas de reportes de maltrato animal:
    - Ver formulario de reporte (/reporte)
    - Procesar reporte (/procesar_reporte)
    """

    def __init__(self, app, conexion):
        """
        Inicializa las rutas de reportes

        Args:
            app: Instancia de Flask
            conexion: Instancia de Conexion
        """
        self.app = app
        self.conexion = conexion
        self.registrar_rutas()

    def registrar_rutas(self):
        """Registra todas las rutas de reportes"""

        @self.app.route('/reporte')
        def reporte():
            """
            Muestra el formulario para reportar maltrato animal
            Requiere que el usuario esté autenticado
            """
            if 'loggedin' not in session:
                flash('Debes iniciar sesión para poder enviar un reporte.', 'danger')
                return redirect(url_for('login'))
            return render_template('reportes/reporte.html')

        @self.app.route('/procesar_reporte', methods=['POST'])
        def procesar_reporte():
            """
            Procesa el envío de un reporte de maltrato animal
            Valida la información y guarda el reporte en la BD
            Puede incluir foto de evidencia
            """
            if 'loggedin' not in session:
                return redirect(url_for('login'))

            if request.method == 'POST':
                # Obtener datos del formulario
                ubicacion = request.form.get('ubicacion')
                descripcion = request.form.get('descripcion_incidente')
                foto_evidencia = request.files.get('foto_evidencia')

                # Validar y guardar la imagen si se subió
                foto_evidencia_url = None
                if foto_evidencia and self.conexion.allowed_file(foto_evidencia.filename, self.app):
                    # Asegurar que el nombre de archivo sea seguro
                    filename = secure_filename(foto_evidencia.filename)
                    filepath = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
                    foto_evidencia.save(filepath)
                    foto_evidencia_url = filename
                else:
                    flash('El archivo de imagen no es válido o no se ha subido. Se creará el reporte sin foto.', 'warning')

                try:
                    # Guardar reporte en BD
                    cur = self.conexion.get_cursor()
                    cur.execute("""
                        INSERT INTO reportes (ubicacion, descripcion_incidente, foto_evidencia_url, estado_reporte)
                        VALUES (%s, %s, %s, 'recibido')
                    """, (ubicacion, descripcion, foto_evidencia_url))
                    self.conexion.commit()
                    cur.close()

                    flash('¡Reporte enviado con éxito! Gracias por tu colaboración.', 'success')
                except Exception as e:
                    flash(f'Ocurrió un error al guardar el reporte: {e}', 'danger')
                    return redirect(url_for('reporte'))

                return redirect(url_for('home'))

            return redirect(url_for('reporte'))
