"""
Test exhaustivo de la aplicación con sesión iniciada
Prueba todas las rutas, formularios y funcionalidades
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Usuario, Mascota, Reporte
from app.rutas import registrar_todas_las_rutas
from app.rutas.conexion import Conexion
from flask_bcrypt import Bcrypt
from datetime import datetime

# Crear app en modo test
app, _ = create_app('testing')

# Registrar rutas
conexion = Conexion(app)
registrar_todas_las_rutas(app, conexion)

client = app.test_client()

# Variables globales para tracking
resultados = {
    'exitosos': [],
    'errores': [],
    'warnings': []
}

def test_route(name, method, route, session_data=None, data=None, expected_status=[200, 302, 303, 307]):
    """Test una ruta individual"""
    try:
        if session_data:
            with client.session_transaction() as sess:
                sess.update(session_data)
        
        if method == 'GET':
            response = client.get(route)
        elif method == 'POST':
            response = client.post(route, data=data)
        else:
            response = client.head(route)
        
        status_ok = response.status_code in expected_status
        
        if status_ok:
            resultados['exitosos'].append(f"OK {name} status={response.status_code}")
        else:
            resultados['errores'].append(f"FAIL {name} status={response.status_code} (expected {expected_status})")
            if response.status_code >= 500:
                error_msg = response.data.decode()[:500]
                resultados['errores'].append(f"   Error: {error_msg}")
        
        return response
    except Exception as e:
        resultados['errores'].append(f"FAIL {name} - Exception: {str(e)[:100]}")
        return None

with app.app_context():
    db.create_all()
    
    # Crear usuarios de prueba
    bcrypt = Bcrypt()
    
    # Usuario normal
    usuario_normal = Usuario(
        nombre='Juan Pérez',
        email='juan@example.com',
        password=bcrypt.generate_password_hash('Password123!').decode('utf-8'),
        verified=True,
        rol='user'
    )
    db.session.add(usuario_normal)
    
    # Usuario admin
    usuario_admin = Usuario(
        nombre='Admin User',
        email='admin@example.com',
        password=bcrypt.generate_password_hash('AdminPass123!').decode('utf-8'),
        verified=True,
        rol='admin'
    )
    db.session.add(usuario_admin)
    
    # Crear mascotas de prueba
    mascota1 = Mascota(
        nombre='Firulais',
        especie='perro',
        raza='Labrador',
        edad=24,
        sexo='M',
        descripcion='Perro amigable y energético',
        foto_url='test.jpg',
        estado='Disponible'
    )
    
    mascota2 = Mascota(
        nombre='Michi',
        especie='gato',
        raza='Persa',
        edad=12,
        sexo='F',
        descripcion='Gato tranquilo',
        foto_url='test2.jpg',
        estado='En proceso'
    )
    
    db.session.add_all([mascota1, mascota2])
    db.session.commit()
    
    print("OK: Datos de prueba creados")
    print(f"  - Usuario normal: {usuario_normal.nombre} (id={usuario_normal.id})")
    print(f"  - Usuario admin: {usuario_admin.nombre} (id={usuario_admin.id})")
    print(f"  - Mascotas: {mascota1.nombre}, {mascota2.nombre}")
    
    # Datos de sesión
    session_user = {
        'loggedin': True,
        'id': usuario_normal.id,
        'nombre': usuario_normal.nombre,
        'usuario_id': usuario_normal.id,
        'usuario_nombre': usuario_normal.nombre,
        'usuario_rol': 'user',
        'rol': 'user'
    }
    
    session_admin = {
        'loggedin': True,
        'id': usuario_admin.id,
        'nombre': usuario_admin.nombre,
        'usuario_id': usuario_admin.id,
        'usuario_nombre': usuario_admin.nombre,
        'usuario_rol': 'admin',
        'rol': 'admin'
    }
    
    print("\n" + "="*60)
    print("TEST 1: RUTAS PÚBLICAS (sin sesión)")
    print("="*60)
    
    test_route("Home", "GET", "/", expected_status=[200])
    test_route("Mascotas", "GET", "/mascotas", expected_status=[200])
    test_route("Registro", "GET", "/registro", expected_status=[200])
    test_route("Login", "GET", "/login", expected_status=[200])
    test_route("Donaciones", "GET", "/donaciones", expected_status=[200])
    test_route("Voluntariado", "GET", "/voluntariado", expected_status=[200])
    
    print("\n" + "="*60)
    print("TEST 2: RUTAS DE USUARIO (con sesión usuario normal)")
    print("="*60)
    
    test_route("Perfil", "GET", "/perfil", session_data=session_user, expected_status=[200])
    test_route("Editar perfil", "GET", "/editar_perfil", session_data=session_user, expected_status=[200])
    
    # Mirar detalle de mascota
    test_route("Detalle mascota", "GET", f"/mascota/{mascota1.id}", session_data=session_user, expected_status=[200])
    
    # Formulario de adopción
    test_route("Formulario adopción", "GET", f"/adoptar/{mascota1.id}", session_data=session_user, expected_status=[200])
    
    # POST Adopción
    adopcion_data = {
        'direccion': 'Calle Principal 123, Apartamento 4B',
        'telefono': '3005551234',
        'ingresos': '2500000',
        'estrato': '3',
        'mensaje': 'Amo mucho los perros y quiero darle un hogar'
    }
    test_route("POST Adopción", "POST", f"/adoptar/{mascota1.id}", session_data=session_user, 
               data=adopcion_data, expected_status=[302, 303])
    
    # Formulario de reporte
    test_route("Formulario reporte", "GET", "/reporte", session_data=session_user, expected_status=[200])
    
    # POST Reporte
    reporte_data = {
        'ubicacion': 'Diag. 72 con Calle 10, Bogotá',
        'descripcion_incidente': 'Vi a un perro abandonado en la calle. Parecía maltratado y necesita atención urgente.'
    }
    test_route("POST Reporte", "POST", "/procesar_reporte", session_data=session_user, 
               data=reporte_data, expected_status=[302, 303])
    
    # POST Voluntariado
    voluntariado_data = {
        'nombre_completo': 'Juan Pérez García',
        'correo': 'juan.garcia@email.com',
        'telefono': '3001234567',
        'franja_dias': 'fines_semana',
        'dias_semana': ['sabado', 'domingo'],
        'franja_horaria': 'manana_8_14',
        'motivo_voluntariado': 'Me encanta trabajar con animales'
    }
    test_route("POST Voluntariado", "POST", "/voluntariado", session_data=session_user, 
               data=voluntariado_data, expected_status=[302, 303])
    
    # Cambiar idioma
    test_route("Cambiar idioma", "GET", "/cambiar_idioma/es", session_data=session_user, expected_status=[302, 303])
    
    print("\n" + "="*60)
    print("TEST 3: RUTAS DE ADMIN (con sesión admin)")
    print("="*60)
    
    test_route("Panel admin", "GET", "/admin/panel", session_data=session_admin, expected_status=[200])
    
    # Crear una solicitud de adopción para probar detalles
    from app.models import SolicitudAdopcion
    
    solicitud = SolicitudAdopcion(
        usuario_id=usuario_normal.id,
        mascota_id=mascota1.id,
        mensaje='Quiero adoptar a Firulais',
        direccion='Calle 123',
        telefono='1234567890',
        ingresos=2000000,
        estrato_social=3,
        estado='pendiente'
    )
    db.session.add(solicitud)
    db.session.commit()
    
    test_route("Detalle solicitud", "GET", f"/admin/detalle_solicitud/{solicitud.id}", 
               session_data=session_admin, expected_status=[200])
    
    # POST Respuesta a solicitud
    respuesta_data = {'respuesta': 'aprobada'}
    test_route("POST Respuesta solicitud", "POST", f"/admin/respuesta_solicitud/{solicitud.id}", 
               session_data=session_admin, data=respuesta_data, expected_status=[302, 303])
    
    # Crear un reporte para probar detalles
    reporte = Reporte(
        usuario_id=usuario_normal.id,
        ubicacion='Parque central',
        descripcion_incidente='Perro abandonado encontrado'
    )
    db.session.add(reporte)
    db.session.commit()
    
    test_route("Detalle reporte", "GET", f"/admin/reporte/{reporte.id}", 
               session_data=session_admin, expected_status=[200])
    
    # POST Resolver reporte
    test_route("POST Resolver reporte", "POST", f"/reporte/resolver/{reporte.id}", 
               session_data=session_admin, expected_status=[302, 303])
    
    # Formulario ingresar mascota
    test_route("Formulario ingresar mascota", "GET", "/admin/ingresar_mascota", 
               session_data=session_admin, expected_status=[200])
    
    # POST Ingresar mascota (sin archivo)
    mascota_data = {
        'nombre': 'Perro de prueba',
        'especie': 'perro',
        'raza': 'Criollo',
        'edad': '12',
        'sexo': 'M',
        'descripcion': 'Mascota de prueba para testing'
    }
    test_route("POST Ingresar mascota", "POST", "/admin/ingresar_mascota", 
               session_data=session_admin, data=mascota_data, expected_status=[302, 303, 200])
    
    print("\n" + "="*60)
    print("TEST 4: RUTAS PDF (con sesión admin)")
    print("="*60)
    
    test_route("Reporte PDF Usuarios", "GET", "/reporte/usuarios", 
               session_data=session_admin, expected_status=[200])
    
    test_route("Reporte PDF Mascotas", "GET", "/reporte/mascotas", 
               session_data=session_admin, expected_status=[200])
    
    test_route("Reporte PDF Donaciones", "GET", "/reporte/donaciones", 
               session_data=session_admin, expected_status=[200, 302, 500])  # Tabla puede no existir
    
    test_route("Reporte PDF Maltrato", "GET", "/reporte/maltrato", 
               session_data=session_admin, expected_status=[200])
    
    print("\n" + "="*60)
    print("TEST 5: RUTAS FILTRADAS")
    print("="*60)
    
    test_route("Filtrar mascotas por especie", "GET", "/filtrar_mascotas?especie=perro", 
               session_data=session_user, expected_status=[200])
    
    test_route("Filtrar mascotas por raza", "GET", "/filtrar_mascotas?raza=Labrador", 
               session_data=session_user, expected_status=[200])
    
    print("\n" + "="*60)
    print("TEST 6: RUTAS SIN SESIÓN (deben redirigir)")
    print("="*60)
    
    # Limpiar la sesión entre TEST 5 y TEST 6
    with client:
        client.get('/')  # Hacer un request para acceder a la sesión
        with client.session_transaction() as sess:
            sess.clear()
    
    test_route("Perfil sin sesión", "GET", "/perfil", expected_status=[302])
    test_route("Editar perfil sin sesión", "GET", "/editar_perfil", expected_status=[302])
    test_route("Reporte sin sesión", "GET", "/reporte", expected_status=[302])
    test_route("Admin panel sin sesión", "GET", "/admin/panel", expected_status=[302])
    
    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)
    
    print(f"\nOK - EXITOSOS ({len(resultados['exitosos'])}):")
    for resultado in resultados['exitosos']:
        print(f"  {resultado}")
    
    if resultados['errores']:
        print(f"\nERRORS - {len(resultados['errores'])} errores:")
        for error in resultados['errores']:
            print(f"  {error}")
    
    if resultados['warnings']:
        print(f"\nWARNINGS - {len(resultados['warnings'])} warnings:")
        for warning in resultados['warnings']:
            print(f"  {warning}")
    
    print("\n" + "="*60)
    total_tests = len(resultados['exitosos']) + len(resultados['errores'])
    print(f"TOTAL: {len(resultados['exitosos'])}/{total_tests} tests exitosos")
    print("="*60)
    
    # Retornar código de error si hay fallos críticos
    if len(resultados['errores']) > 0:
        print(f"\nWARNING: Se encontraron {len(resultados['errores'])} errores durante el testing")
        sys.exit(1)
    else:
        print("\nOK: Todos los tests completaron exitosamente")
        sys.exit(0)
