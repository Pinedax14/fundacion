"""
Módulo de rutas para la página de inicio y donaciones
Contiene las rutas públicas principales de la fundación
"""

from flask import render_template, request, redirect, url_for, flash, g, session
from app.rutas.decoradores import admin_required_factory


class RutasHome:
    """
    Gestiona las rutas principales de la aplicación:
    - Home (/home)
    - Voluntariado (/voluntariado)
    - Donaciones (/donaciones)
    - Pruebas (/pruebas)
    """

    def __init__(self, app, conexion):
        """
        Inicializa las rutas home con la aplicación Flask y conexión BD

        Args:
            app: Instancia de Flask
            conexion: Instancia de Conexion (contiene .mysql y .bcrypt)
        """
        self.app = app
        self.conexion = conexion
        self.bcrypt = conexion.bcrypt
        self.admin_required = admin_required_factory(app)
        self.registrar_rutas()

    def registrar_rutas(self):
        """Registra todas las rutas de home con el decorador de Flask"""

        @self.app.route('/')
        @self.app.route('/home')
        def home():
            # Página principal de la fundación
            return render_template('home/home.html')

        @self.app.before_request
        def cargar_usuario():
            """
            Hook que se ejecuta antes de cada request.
            Carga los datos del usuario logueado en g.usuario si existe sesión.
            Omite esto para archivos estáticos.
            """
            # No procesar para archivos estáticos
            if request.path.startswith('/static/'):
                return

            # Si hay sesión, cargar usuario desde BD
            if 'loggedin' in session:
                user_id = session.get('id')

                if user_id is not None:
                    cursor = self.conexion.get_cursor()
                    try:
                        cursor.execute(
                            'SELECT * FROM usuarios WHERE id = %s',
                            (user_id,)
                        )
                        g.usuario = cursor.fetchone()
                    except Exception as e:
                        print(f"Error al cargar usuario: {e}")
                        g.usuario = None
                    finally:
                        cursor.close()
                else:
                    g.usuario = None
            else:
                g.usuario = None

        @self.app.route('/voluntariado', methods=['GET', 'POST'])
        def voluntariado():
            """
            GET: Muestra formulario para ser voluntario
            POST: Procesa la solicitud de voluntariado y la guarda en BD
            """
            if request.method == 'POST':
                # Obtener datos del formulario
                nombre = request.form.get('nombre_completo')
                correo = request.form.get('correo')
                telefono = request.form.get('telefono')
                franja_dias = request.form.get('franja_dias')          # fines_semana/entre_semana
                dias_semana = request.form.getlist('dias_semana')      # múltiples checkboxes
                franja_horaria = request.form.get('franja_horaria')    # manana_8_14/tarde_15_19
                motivo = request.form.get('motivo_voluntariado')

                # Convertir lista de días a string
                dias_semana_texto = ", ".join(dias_semana) if dias_semana else None

                # Validaciones básicas
                if not nombre or not correo or not telefono or not franja_dias or not franja_horaria or not motivo:
                    flash('Por favor, completa todos los campos obligatorios.', 'warning')
                    return render_template('home/voluntariado.html')

                # Guardar en la base de datos
                cur = self.conexion.get_cursor()
                sql = """
                INSERT INTO solicitudes_voluntariado
                    (nombre_completo, correo, telefono, franja_dias, dias_semana, franja_horaria, motivo_voluntariado)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(sql, (nombre, correo, telefono, franja_dias, dias_semana_texto, franja_horaria, motivo))
                self.conexion.commit()
                cur.close()

                flash('¡Gracias por querer ser voluntario! Pronto nos pondremos en contacto contigo.', 'success')
                return redirect(url_for('home'))

            return render_template('home/voluntariado.html')

        @self.app.route('/donaciones', methods=['GET'])
        def donaciones():
            """Muestra página de donaciones"""
            return render_template('home/donaciones.html')

        @self.app.route('/pruebas', methods=['GET'])
        def pruebas():
            """Página de pruebas (temporal)"""
            return render_template('home/pruebas.html')
