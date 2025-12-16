from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
from flask import send_file
from flask import render_template, request, redirect, url_for, session, flash
from functools import wraps
from werkzeug.utils import secure_filename
import MySQLdb.cursors
import os
import uuid
from flask import Flask
from flask import g, session
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from email.mime.image import MIMEImage

 
REMITENTE = "almasconcola@gmail.com"  # tu nueva cuenta
CONTRASENA_APP = "xwyi ahgu cqas qvvp"  # 16 caracteres generados

 


# Decoradores y helpers

def admin_required_factory(app):
    """Crea un decorador que verifica si el usuario es admin"""
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'loggedin' not in session or session.get('rol') != 'admin':
                flash('Acceso no autorizado. Debes ser administrador.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return admin_required


#CLASE PARA LAS RUTAS HOME Y DONACIONES

class RutasHome:
    def __init__(self, app, conexion): #se crea el constructor 
        self.app = app                  # instancia de flask
        self.conexion = conexion        # instancia de Conexion (tiene .mysql y .bcrypt)
        self.bcrypt = conexion.bcrypt
        # uso del decorador admin creado arriba
        self.admin_required = admin_required_factory(app)
        self.registrar_rutas()

    def registrar_rutas(self):  
        @self.app.route('/')    # ruta principal tanto para / como para /home
        @self.app.route('/home')
        def home():
            return render_template('home.html') 
        
        @self.app.before_request
        def cargar_usuario():
 
            if request.path.startswith('/static/'):
                return

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
                        g.usuario = None
                    finally:
                        cursor.close()
                else:
                    g.usuario = None
            else:
                g.usuario = None
           


        @self.app.route('/voluntariado', methods=['GET', 'POST'])
        def voluntariado():
            if request.method == 'POST':
                nombre = request.form.get('nombre_completo')
                correo = request.form.get('correo')
                telefono = request.form.get('telefono')

                franja_dias = request.form.get('franja_dias')          # fines_de_semana / entre_semana
                dias_semana = request.form.getlist('dias_semana')      # lista de checkboxes
                franja_horaria = request.form.get('franja_horaria')    # manana_8_14 / tarde_15_19

                motivo = request.form.get('motivo_voluntariado')

        
                dias_semana_texto = ", ".join(dias_semana) if dias_semana else None

        # validaciones básicas
                if not nombre or not correo or not telefono or not franja_dias or not franja_horaria or not motivo:
                    flash('Por favor, completa todos los campos obligatorios.', 'warning')
                    return render_template('voluntariado.html')

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

            return render_template('voluntariado.html')

               

        @self.app.route('/donaciones', methods=['GET']) # ruta para donaciones
        def donaciones():                       
           return render_template('donaciones.html')



#CLASE PARA LAS RUTAS DE SESION, REGISTRO Y PERFIL



# Configuración del correo
REMITENTE = "almasconcola@gmail.com"  # tu correo de envío
CONTRASENA_APP = "xwyi ahgu cqas qvvp"  # token de app generado en Gmail

class RutasAuth:
    def __init__(self, app, conexion):
        self.app = app
        self.conexion = conexion
        self.mysql = conexion.mysql
        self.bcrypt = conexion.bcrypt
        self.admin_required = admin_required_factory(app)
        self.registrar_rutas()
        
        

        


    def registrar_rutas(self):
        @self.app.route('/registro', methods=['GET', 'POST'])
        def registro():
            msg = ''
            if request.method == 'POST':
                nombre = request.form.get('nombre')
                email = request.form.get('email')
                password = request.form.get('password')
                confirmar_password = request.form.get('confirmar_password')

                print(f"[DEBUG] Contraseña: '{password}'")
                print(f"[DEBUG] Confirmación: '{confirmar_password}'")
                print(f"¿Son iguales? {password == confirmar_password}")

                cur = self.conexion.get_cursor()
                cur.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
                cuenta = cur.fetchone()

                if cuenta:
                    msg = '¡La cuenta de correo electrónico ya existe!'
                elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                    msg = '¡Dirección de correo electrónico no válida!'
                elif password != confirmar_password:
                    msg = '¡Las contraseñas no coinciden!'
                elif len(password) < 8 or not re.search(r"[0-9]", password) or not re.search(r"[!@#$%^&*()-_=+{};:,<.>]", password):
                    msg = 'La contraseña debe tener al menos 8 caracteres, un número y un símbolo especial.'
                else:
                    hash_password = self.bcrypt.generate_password_hash(password).decode('utf-8')
                    cur.execute('INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)',
                                (nombre, email, hash_password, 'user'))
                    self.conexion.commit()

                    # Obtener ID del nuevo usuario
                    cur.execute('SELECT id FROM usuarios WHERE email = %s', (email,))
                    nuevo_usuario = cur.fetchone()
                    id_usuario = nuevo_usuario['id']

                    # Generar código de verificación
                    codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    cur.execute('INSERT INTO verificaciones (id_usuario, codigo, fecha_creacion, usado) VALUES (%s, %s, NOW(), %s)',
                                (id_usuario, codigo, False))
                    self.conexion.commit()

                    # Enviar correo con el código
                    asunto = "Código de verificación de tu cuenta"
                    cuerpo = f"Hola {nombre},\n\nGracias por registrarte.\nTu código de verificación es: {codigo}\n\nIngresa este código en la página de verificación para activar tu cuenta."
                    mensaje = MIMEMultipart()
                    mensaje['From'] = REMITENTE
                    mensaje['To'] = email
                    mensaje['Subject'] = asunto
                    cuerpo_html = render_template('correo_verificacion.html', nombre=nombre, codigo=codigo)
                    mensaje.attach(MIMEText(cuerpo_html, 'html'))

                    with open("app/static/images/logo.jpg", "rb") as f:
                         imagen = MIMEImage(f.read())
                         imagen.add_header('Content-ID', '<logo_fundacion>')
                         imagen.add_header('Content-Disposition', 'inline', filename="logo.jpg")
                         mensaje.attach(imagen)

                    try:
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(REMITENTE, CONTRASENA_APP)
                        server.sendmail(REMITENTE, email, mensaje.as_string())
                        server.quit()
                        flash('¡Te has registrado exitosamente! Se ha enviado un correo de verificación.', 'success')
                        cur.close()
                        return redirect(url_for('verificar_email'))
                    except Exception as e:
                        flash(f'Error al enviar el correo de verificación: {e}', 'danger')

                cur.close()
            return render_template('registro.html', msg=msg)

        @self.app.route('/verificar_email', methods=['GET', 'POST'])
        def verificar_email():
            msg = ''
            if request.method == 'POST':
                email = request.form.get('email')
                codigo = request.form.get('codigo')                                                        

                cur = self.conexion.get_cursor()
                cur.execute('SELECT id FROM usuarios WHERE email = %s', (email,))
                usuario = cur.fetchone()

                if not usuario:
                    msg = 'Correo no registrado.'
                else:
                    cur.execute('SELECT * FROM verificaciones WHERE id_usuario = %s AND codigo = %s AND usado = FALSE',
                                (usuario['id'], codigo))
                    verificacion = cur.fetchone()

                    if verificacion:
                        cur.execute('UPDATE verificaciones SET usado = TRUE WHERE id = %s', (verificacion['id'],))
                        self.conexion.commit()
                        flash('¡Cuenta verificada exitosamente! Ahora puedes iniciar sesión.', 'success')
                        cur.close()
                        return redirect(url_for('login'))
                    else:
                        msg = 'Código incorrecto o ya usado.'
                cur.close()
            return render_template('verificar_email.html', msg=msg)

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            msg = ''
            if 'loggedin' in session:
                return redirect(url_for('home'))

            if request.method == 'POST':
                email = request.form.get('email')
                password = request.form.get('password')

                cur = self.conexion.get_cursor()
                cur.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
                cuenta = cur.fetchone()

                if cuenta and self.bcrypt.check_password_hash(cuenta['password'], password):
                    cur.execute('SELECT * FROM verificaciones WHERE id_usuario = %s AND usado = FALSE', (cuenta['id'],))
                    pendiente = cur.fetchone()
                    if pendiente:
                        msg = 'Debes verificar tu cuenta antes de iniciar sesión.'
                    else:
                        session['loggedin'] = True
                        session['id'] = cuenta['id']
                        session['nombre'] = cuenta['nombre']
                        session['rol'] = cuenta['rol']
                        flash(f"¡Bienvenido de vuelta, {session['nombre']}!", 'success')
                        cur.close()
                        return redirect(url_for('home'))
                else:
                    msg = '¡Correo electrónico o contraseña incorrectos!'
                cur.close()
            return render_template('login.html', msg=msg)

        @self.app.route('/logout')
        def logout():
            session.clear()
            flash('Has cerrado sesión exitosamente.', 'info')
            return redirect(url_for('home'))

        @self.app.route('/perfil')
        def perfil():
            if 'loggedin' not in session:
                flash('Debes iniciar sesión para ver tu perfil.', 'warning')
                return redirect(url_for('login'))

            user_id = session['id']
            cursor = self.conexion.get_cursor()
            cursor.execute('SELECT nombre, email, fecha_registro FROM usuarios WHERE id = %s', [user_id])
            usuario = cursor.fetchone()

            cursor.execute(''' 
                SELECT s.id, s.fecha_solicitud, s.estado_solicitud, m.nombre as mascota_nombre, m.foto_url as mascota_foto
                FROM solicitudes_adopcion s
                JOIN mascotas m ON s.id_mascota = m.id  
                WHERE s.id_usuario = %s
                ORDER BY s.fecha_solicitud DESC
            ''', [user_id])
            solicitudes = cursor.fetchall()
            cursor.close()

            return render_template('perfil.html', usuario=usuario, solicitudes=solicitudes)
        ALLOWED_EXTENSIONS_PERFIL = {'png', 'jpg', 'jpeg', 'gif'}

        def allowed_file_perfil(filename):
                return '.' in filename and \
                    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_PERFIL
        
        


        @self.app.route('/editar_perfil', methods=['GET', 'POST'])
        def editar_perfil():
            if 'loggedin' not in session:
                flash('Debes iniciar sesión para editar tu perfil.', 'warning')
                return redirect(url_for('login'))
            


            user_id = session['id']
            cursor = self.conexion.get_cursor()
            cursor.execute('SELECT * FROM usuarios WHERE id = %s', (user_id,))
            usuario = cursor.fetchone()

            if request.method == 'POST':
                nombre = request.form.get('nombre')
                email = request.form.get('email')
                password_actual = request.form.get('password_actual')
                password_nueva = request.form.get('password_nueva')
                password_confirm = request.form.get('password_confirm')
                foto_file = request.files.get('foto_perfil')
                if foto_file and foto_file.filename != '':
                # Validar tipo de archivo
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    extension = foto_file.filename.rsplit('.', 1)[1].lower()
                    if extension not in allowed_extensions:
                        flash('Solo se permiten imágenes (png, jpg, jpeg, gif)', 'danger')
                        return redirect(url_for('editar_perfil'))
                    import uuid
                    filename = f"{uuid.uuid4().hex}.{extension}"
                    upload_folder = os.path.join(os.getcwd(), 'app', 'static', 'uploads', 'perfiles')

                    app.logger.info("Ruta absoluta: %s", upload_folder)


                    if not os.path.exists(upload_folder):
                         os.makedirs(upload_folder)
                    filepath = os.path.join('app/static/uploads/perfiles/', filename)
                    print("Ruta de guardado:", filepath)


                    # Guardar la imagen
                    foto_file.save(filepath)

                    usuario['foto_perfil'] = filename

                    cursor.execute('UPDATE usuarios SET foto_perfil=%s WHERE id=%s', (filename, user_id))
                    self.conexion.commit()



                errores = []

                if not nombre or not email:
                    errores.append("El nombre y correo son obligatorios.")

                cambiar_password = password_nueva and password_actual

                if cambiar_password:
                    if not self.bcrypt.check_password_hash(usuario['password'], password_actual):
                        errores.append("La contraseña actual no es correcta.")
                    elif password_nueva != password_confirm:
                        errores.append("La nueva contraseña no coincide con la confirmación.")
                    elif len(password_nueva) < 8:
                        errores.append("La nueva contraseña debe tener al menos 8 caracteres.")

                if errores:
                    for e in errores:
                        flash(e, "danger")
                else:
                    cursor.execute('UPDATE usuarios SET nombre=%s, email=%s WHERE id=%s', (nombre, email, user_id))
                    self.conexion.commit()
                    session['nombre'] = nombre

                    if cambiar_password:
                        hashed_password = self.bcrypt.generate_password_hash(password_nueva).decode('utf-8')
                        cursor.execute('UPDATE usuarios SET password=%s WHERE id=%s', (hashed_password, user_id))
                        self.conexion.commit()

                    flash("¡Perfil actualizado correctamente!", "success")
                    cursor.close()
                    return redirect(url_for('editar_perfil'))

            return render_template('editar_perfil.html', usuario=usuario)

        @self.app.route('/cambiar_password', methods=['POST'])
        def cambiar_password():
            if 'loggedin' not in session:
                return redirect(url_for('login'))

            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if new_password != confirm_password:
                flash('Las nuevas contraseñas no coinciden.', 'danger')
                return redirect(url_for('perfil'))

            cursor = self.conexion.get_cursor()
            cursor.execute('SELECT password FROM usuarios WHERE id = %s', [session['id']])
            user = cursor.fetchone()

            if user and self.bcrypt.check_password_hash(user['password'], current_password):
                new_hash_password = self.bcrypt.generate_password_hash(new_password).decode('utf-8')
                cursor.execute('UPDATE usuarios SET password = %s WHERE id = %s', (new_hash_password, session['id']))
                self.conexion.commit()
                flash('¡Contraseña actualizada exitosamente!', 'success')
            else:
                flash('La contraseña actual es incorrecta.', 'danger')
            cursor.close()
            return redirect(url_for('perfil'))

        @self.app.route('/eliminar_cuenta')
        def eliminar_cuenta():
            flash('La funcionalidad para eliminar la cuenta aún está en construcción.', 'info')
            return redirect(url_for('perfil'))



# --------------------------
# CLASE RutasMascotas
# --------------------------
class RutasMascotas:
    def __init__(self, app, conexion):
        self.app = app
        self.conexion = conexion
        self.mysql = conexion.mysql
        self.registrar_rutas()

    def registrar_rutas(self):
        @self.app.route('/mascotas')
        def mascotas():
            cursor = self.conexion.get_cursor()
            cursor.execute("SELECT id, nombre, estado, fecha_ingreso FROM mascotas ORDER BY estado ASC")
            lista_mascotas = cursor.fetchall()
            cursor.close()
            return render_template('mascotas.html', mascotas=lista_mascotas)


        @self.app.route('/filtrar_mascotas', methods=['GET'])
        def filtrar_mascotas():
            especie = request.args.get('especie')
            raza = request.args.get('raza')
            edad = request.args.get('edad')
            sexo = request.args.get('sexo')

            sql_query = "SELECT * FROM mascotas WHERE 1=1"
            params = []

            if especie:
                sql_query += " AND especie = %s"
                params.append(especie)

            if raza:
                sql_query += " AND raza LIKE %s"
                params.append(f"%{raza}%")

            if edad:
                sql_query += " AND edad = %s"
                params.append(edad)

            if sexo:
                sql_query += " AND sexo = %s"
                params.append(sexo)

            cur = self.conexion.get_cursor()
            cur.execute(sql_query, params)

            mascotas_filtradas = cur.fetchall()
            column_names = [desc[0] for desc in cur.description] if cur.description else []
            cur.close()

            lista_de_mascotas = []
            for row in mascotas_filtradas:
                lista_de_mascotas.append(dict(zip(column_names, row)))

            return render_template('mascotas.html', mascotas=lista_de_mascotas)


        @self.app.route('/mascota/<int:mascota_id>')
        def detalle_mascota(mascota_id):
            cursor = self.conexion.get_cursor()
            cursor.execute('SELECT * FROM mascotas WHERE id = %s', [mascota_id])
            mascota = cursor.fetchone()
            cursor.close()
            if mascota:
                return render_template('detalle_mascota.html', mascota=mascota)
            return 'Mascota no encontrada', 404


        @self.app.route('/adoptar/<int:mascota_id>', methods=['GET', 'POST'])
        def solicitar_adopcion(mascota_id):
            if 'loggedin' not in session:
                flash('Es necesario iniciar sesión para poder adoptar.', 'danger')
                return redirect(url_for('login'))

            cursor = self.conexion.get_cursor()
            cursor.execute('SELECT * FROM mascotas WHERE id = %s', [mascota_id])
            mascota = cursor.fetchone()

            if not mascota or mascota['estado'] != 'Disponible':
                flash('Esta mascota no está disponible para adopción.', 'warning')
                return redirect(url_for('mascotas'))

            if request.method == 'POST':
                id_usuario = session['id']
                direccion = request.form.get('direccion')
                telefono = request.form.get('telefono')
                ingresos = request.form.get('ingresos')
                estrato = request.form.get('estrato')
                mensaje = request.form.get('mensaje')

                cursor.execute('''
                    INSERT INTO solicitudes_adopcion 
                    (id_usuario, id_mascota, fecha_solicitud, estado_solicitud, mensaje, direccion, telefono, ingresos, estrato_social) 
                    VALUES (%s, %s, NOW(), 'pendiente', %s, %s, %s, %s, %s)
                ''', (id_usuario, mascota_id, mensaje, direccion, telefono, ingresos, estrato))

                cursor.execute("UPDATE mascotas SET estado = 'En proceso' WHERE id = %s", [mascota_id])
                self.conexion.commit()
                cursor.close()

                flash('¡Tu solicitud de adopción ha sido enviada con éxito!', 'success')
                return redirect(url_for('mascotas'))

            return render_template('solicitud_adopcion.html', mascota=mascota)


        @self.app.route('/eliminar_solicitud/<int:solicitud_id>')
        def eliminar_solicitud(solicitud_id):
            if 'loggedin' not in session:
                flash('Debes iniciar sesión para realizar esta acción.', 'warning')
                return redirect(url_for('login'))
            user_id = session['id']
            cursor = self.conexion.get_cursor()
            cursor.execute('SELECT estado_solicitud FROM solicitudes_adopcion WHERE id = %s AND id_usuario = %s', (solicitud_id, user_id))
            solicitud = cursor.fetchone()

            if not solicitud:
                flash('Solicitud no encontrada o no pertenece al usuario.', 'danger')
                cursor.close()
                return redirect(url_for('perfil'))

            if solicitud['estado_solicitud'].lower() != 'rechazada':
                flash('Solo puedes eliminar solicitudes rechazadas.', 'warning')
                cursor.close()
                return redirect(url_for('perfil'))

            cursor.execute('DELETE FROM solicitudes_adopcion WHERE id = %s', [solicitud_id])
            self.conexion.commit()
            cursor.close()
            flash('Solicitud rechazada eliminada correctamente.', 'success')
            return redirect(url_for('perfil'))


        @self.app.route('/cancelar_solicitud/<int:solicitud_id>')
        def cancelar_solicitud(solicitud_id):
            if 'loggedin' not in session:
                return redirect(url_for('login'))

            cursor = self.conexion.get_cursor()
            cursor.execute('SELECT id_mascota FROM solicitudes_adopcion WHERE id = %s AND id_usuario = %s', (solicitud_id, session['id']))
            solicitud = cursor.fetchone()

            if solicitud:
                id_mascota = solicitud['id_mascota']
                cursor.execute("UPDATE mascotas SET estado = 'Disponible' WHERE id = %s", [id_mascota])
                cursor.execute('DELETE FROM solicitudes_adopcion WHERE id = %s', [solicitud_id])
                self.conexion.commit()
                flash('Tu solicitud de adopción ha sido cancelada.', 'success')
            else:
                flash('No se pudo cancelar la solicitud.', 'danger')
            cursor.close()
            return redirect(url_for('perfil'))


# --------------------------
# CLASE RutasReportes
# --------------------------
class RutasReportes:
    def __init__(self, app, conexion):
        self.app = app
        self.conexion = conexion
        self.registrar_rutas()

    def registrar_rutas(self):
        @self.app.route('/reporte')
        def reporte():
            if 'loggedin' not in session:
                flash('Debes iniciar sesión para poder enviar un reporte.', 'danger')
                return redirect(url_for('login'))
            return render_template('reporte.html')


        @self.app.route('/procesar_reporte', methods=['POST'])
        def procesar_reporte():
            print("procesar_reporte llamado")  # <-- Agrega esta línea

            if 'loggedin' not in session:
                return redirect(url_for('login'))

            if request.method == 'POST':
                ubicacion = request.form.get('ubicacion')
                descripcion = request.form.get('descripcion_incidente')
                foto_evidencia = request.files.get('foto_evidencia')
                print("Archivo recibido:", foto_evidencia)
                print("Nombre del archivo:", foto_evidencia.filename if foto_evidencia else "Sin archivo")
                print("UPLOAD_FOLDER:", self.app.config['UPLOAD_FOLDER'])

                # Validar y guardar la imagen
                if foto_evidencia and self.conexion.allowed_file(foto_evidencia.filename, self.app):
                    filename = secure_filename(foto_evidencia.filename)
                    filepath = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
                    foto_evidencia.save(filepath)
                    foto_evidencia_url = filename
                else:
                    foto_evidencia_url = None
                    flash('El archivo de imagen no es válido o no se ha subido. Se creará el reporte sin foto.', 'warning')

                try:
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


# --------------------------
# CLASE RutasAdmin
# --------------------------
class RutasAdmin:
    def __init__(self, app, conexion):
        self.app = app
        self.conexion = conexion
        self.bcrypt = conexion.bcrypt
        # crear decorador admin que use la misma session/contexto
        self.admin_required = admin_required_factory(app)
        self.registrar_rutas()

    def registrar_rutas(self):
        @self.app.route('/admin/panel')
        @self.admin_required
        def admin_panel():
            cursor = self.conexion.get_cursor()

            query_solicitudes = """
                SELECT s.id, u.nombre AS usuario_nombre, m.nombre AS mascota_nombre, 
                       s.fecha_solicitud, s.estado_solicitud 
                FROM solicitudes_adopcion s 
                JOIN usuarios u ON s.id_usuario = u.id 
                JOIN mascotas m ON s.id_mascota = m.id 
                WHERE TRIM(LOWER(s.estado_solicitud)) IN ('pendiente', 'en proceso')
                ORDER BY s.fecha_solicitud DESC
            """
            cursor.execute(query_solicitudes)
            solicitudes = cursor.fetchall()

            cursor.execute("SELECT * FROM reportes ORDER BY fecha_reporte DESC")
            reportes = cursor.fetchall()

            cursor.close()
            return render_template('admin_panel.html', solicitudes=solicitudes, reportes=reportes,)


        @self.app.route('/admin/detalle_solicitud/<int:solicitud_id>')
        @self.admin_required
        def detalle_solicitud(solicitud_id):
            cursor = self.conexion.get_cursor()
            query = """
                SELECT s.*, u.nombre AS usuario_nombre, u.email AS usuario_email,
                       m.nombre AS mascota_nombre, m.foto_url AS mascota_foto
                FROM solicitudes_adopcion s
                JOIN usuarios u ON s.id_usuario = u.id
                JOIN mascotas m ON s.id_mascota = m.id
                WHERE s.id = %s
            """
            cursor.execute(query, [solicitud_id])
            solicitud = cursor.fetchone()
            cursor.close()
            if solicitud:
                return render_template('detalle_solicitud.html', solicitud=solicitud)
            flash('Solicitud no encontrada.', 'danger')
            return redirect(url_for('admin_panel'))


        @self.app.route('/admin/respuesta_solicitud/<int:solicitud_id>', methods=['POST'])
        @self.admin_required
        def respuesta_solicitud(solicitud_id):
            respuesta = request.form.get('respuesta')

            if respuesta not in ['aprobada', 'rechazada']:
                flash('Respuesta inválida. Se recibió un valor incorrecto desde el formulario.', 'danger')
                return redirect(url_for('admin_panel'))

            try:
                cursor = self.conexion.get_cursor()

                cursor.execute("UPDATE solicitudes_adopcion SET estado_solicitud = %s WHERE id = %s", (respuesta, solicitud_id))

                cursor.execute('SELECT id_mascota FROM solicitudes_adopcion WHERE id = %s', [solicitud_id])
                resultado = cursor.fetchone()

                if resultado:
                    id_mascota = resultado['id_mascota']
                    nuevo_estado_mascota = 'Adoptado' if respuesta == 'aprobada' else 'Disponible'
                    cursor.execute("UPDATE mascotas SET estado = %s WHERE id = %s", (nuevo_estado_mascota, id_mascota))

                self.conexion.commit()
                cursor.close()
                flash(f'La solicitud ha sido marcada como \"{respuesta}\".', 'success')
                return redirect(url_for('admin_panel'))

            except Exception as e:
                flash(f'Ocurrió un error de base de datos: {e}', 'danger')
                return redirect(url_for('admin_panel'))


        @self.app.route('/admin/reporte/<int:reporte_id>')
        @self.admin_required
        def detalle_reporte(reporte_id):
            cursor = self.conexion.get_cursor()
            cursor.execute("SELECT * FROM reportes WHERE id = %s", [reporte_id])
            reporte = cursor.fetchone()
            cursor.close()

            if not reporte:
                flash('El reporte no fue encontrado.', 'warning')
                return redirect(url_for('admin_panel'))

            return render_template('detalle_reporte.html', reporte=reporte)


        @self.app.route('/reporte/resolver/<int:reporte_id>', methods=['POST'])
        @self.admin_required
        def marcar_reporte_resuelto(reporte_id):
            try:
                cur = self.conexion.get_cursor()
                cur.execute("UPDATE reportes SET estado_reporte = 'resuelto' WHERE id = %s", [reporte_id])
                self.conexion.commit()
                cur.close()
                flash('El reporte ha sido marcado como resuelto.', 'success')
            except Exception as e:
                flash(f'Error al actualizar el reporte: {e}', 'danger')
            return redirect(url_for('admin_panel'))


        @self.app.route('/reporte/eliminar/<int:reporte_id>', methods=['POST'])
        @self.admin_required
        def eliminar_reporte(reporte_id):
            try:
                cursor = self.conexion.get_cursor()
                cursor.execute("SELECT foto_evidencia_url FROM reportes WHERE id = %s", [reporte_id])
                reporte = cursor.fetchone()
                if reporte and reporte['foto_evidencia_url']:
                    try:
                        ruta_foto = os.path.join(self.app.static_folder, reporte['foto_evidencia_url'])
                        if os.path.exists(ruta_foto):
                            os.remove(ruta_foto)
                    except Exception as e:
                        print(f"No se pudo eliminar el archivo de imagen: {e}")

                cursor.execute("DELETE FROM reportes WHERE id = %s", [reporte_id])
                self.conexion.commit()
                cursor.close()
                flash('El reporte ha sido eliminado correctamente.', 'success')
            except Exception as e:
                flash(f'Error al eliminar el reporte: {e}', 'danger')
            return redirect(url_for('admin_panel'))
        
        @self.app.route('/admin/ingresar_mascota', methods=['GET', 'POST'])
        @self.admin_required
        def ingresar_mascota():
            import traceback
            if request.method == 'POST':
                nombre = request.form.get('nombre')
                especie = request.form.get('especie') 
                raza = request.form.get('raza') 
                edad = request.form.get('edad') 
                sexo = request.form.get('sexo') 
                descripcion = request.form.get('descripcion') 
                foto = request.files.get('foto')

                print("\n=== DEBUG: Datos del formulario ===")
                print(f"nombre: {nombre}")
                print(f"especie: {especie}")
                print(f"raza: {raza}")
                print(f"edad: {edad}")
                print(f"sexo: {sexo}")
                print(f"descripcion: {descripcion}")
                print(f"foto: {foto.filename if foto else 'No subida'}")

                campos_obligatorios = {
                    'nombre': nombre,
                    'especie': especie,
                    'sexo': sexo,
                    'descripcion': descripcion
                }

                for campo, valor in campos_obligatorios.items():
                    if not valor or valor.strip() == '':
                        flash(f'El campo {campo} es obligatorio.', 'danger')
                        return redirect(url_for('ingresar_mascota'))

                foto_url = None
                if foto:
                    
                    extension = ".jpg"
                    nombre_base = secure_filename(nombre.replace(" ", "_"))
                    nombre_archivo = f"{nombre_base}{extension}"
                    ruta_guardado = os.path.join(self.app.static_folder, 'images', nombre_archivo)
                    contador = 1
                    while os.path.exists(ruta_guardado):
                        nombre_archivo = f"{nombre_base}_{contador}{extension}"
                        ruta_guardado = os.path.join(self.app.static_folder, 'images', nombre_archivo)
                        contador += 1
                    foto.save(ruta_guardado)
                    foto_url = f'images/{nombre_archivo}'
                    print(f"[DEBUG] Foto guardada como: {foto_url}")
                try:
                    cursor = self.conexion.get_cursor()
                    cursor.execute("""
                        INSERT INTO mascotas (nombre, especie, raza, edad, sexo, descripcion, foto_url, estado)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (nombre, especie, raza, edad, sexo, descripcion, foto_url, 'Disponible'))
                    print("[DEBUG] Consulta SQL ejecutada") 
                    self.conexion.commit()
                    print("[DEBUG 1] Commit realizado")
                    cursor.close()
                    print("[DEBUG 2] Cursor cerrado")
                    flash('Mascota agregada correctamente.', 'success')
                    print("[DEBUG 3] Flash configurado")
                    return redirect(url_for('admin_panel'))
                except Exception as e:
                    print(f"\n=== DEBUG ERROR: Traceback completo ===")
                    traceback.print_exc()
                    print(f"=== Fin del error ===\n")
                    flash(f'Ocurrió un error al agregar la mascota: {e}', 'danger')
                    return redirect(url_for('ingresar_mascota'))
                
            return render_template('ingreso_mascota.html')
        
        @self.app.route('/recibir_donacion', methods=['POST'])
        @self.admin_required
        def recibir_donacion():
            

            return redirect(url_for('admin_panel'))
        
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
        
from app.conexion import Conexion
conexion = Conexion(app)
rutas_home = RutasHome(app, conexion)


rutas_auth = RutasAuth(app, conexion)
rutas_mascotas = RutasMascotas(app, conexion)
rutas_reportes = RutasReportes(app, conexion)
rutas_admin = RutasAdmin(app, conexion)
        

from app.rutaspdf import RutasPDF, RutasIdioma
rutas_pdf = RutasPDF(app, conexion)
rutas_idioma = RutasIdioma(app, conexion)
if __name__ == '__main__':

    print("Iniciando servidor Flask...")
    print("Abre http://localhost:5000 en tu navegador")
    app.run(debug=True, host='0.0.0.0', port=5000)




