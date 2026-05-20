#!/usr/bin/env python
"""
Script de prueba para validar el nuevo campo fecha_nacimiento en el registro
"""

from dotenv import load_dotenv
from datetime import datetime, date, timedelta

load_dotenv()

from app import create_app
from app.rutas.conexion import Conexion
from app.rutas import registrar_todas_las_rutas

app, db = create_app('development')
conexion = Conexion(app)
registrar_todas_las_rutas(app, conexion)

def test_registro_con_fecha():
    """Prueba el registro con fecha de nacimiento válida"""
    print("\n=== PRUEBA 1: Registro con fecha válida ===")
    
    with app.test_client() as client:
        # Fecha válida (mayor de 13 años)
        fecha_valida = (date.today() - timedelta(days=8000)).strftime('%Y-%m-%d')
        response = client.post('/registro', data={
            'nombre': 'Juan FechaNacimiento',
            'email': f'juan_fecha_{datetime.now().timestamp()}@test.com',
            'fecha_nacimiento': fecha_valida,
            'password': 'Secure@123456',
            'confirmar_password': 'Secure@123456'
        }, follow_redirects=True)
        
        print(f"Status: {response.status_code}")
        if 'Verificar Cuenta' in response.get_data(as_text=True):
            print("RESULTADO: Registro exitoso, redirigido a verificación de email")
            return True
        else:
            print("RESULTADO: Error en el registro")
            print(response.get_data(as_text=True)[:500])
            return False

def test_registro_fecha_futura():
    """Prueba con fecha futura (debe fallar)"""
    print("\n=== PRUEBA 2: Registro con fecha futura (debe fallar) ===")
    
    with app.test_client() as client:
        fecha_futura = (date.today() + timedelta(days=100)).strftime('%Y-%m-%d')
        response = client.post('/registro', data={
            'nombre': 'Maria FechaFutura',
            'email': f'maria_futura_{datetime.now().timestamp()}@test.com',
            'fecha_nacimiento': fecha_futura,
            'password': 'Secure@123456',
            'confirmar_password': 'Secure@123456'
        })
        
        body = response.get_data(as_text=True)
        print(f"Status: {response.status_code}")
        if 'no puede ser en el futuro' in body:
            print("RESULTADO: Validacion correcta, fecha futura rechazada")
            return True
        else:
            print("RESULTADO: No se validó correctamente")
            return False

def test_registro_fecha_muy_antigua():
    """Prueba con fecha muy antigua (más de 150 años, debe fallar)"""
    print("\n=== PRUEBA 3: Registro con fecha muy antigua (debe fallar) ===")
    
    with app.test_client() as client:
        fecha_antigua = (date.today() - timedelta(days=200*365)).strftime('%Y-%m-%d')
        response = client.post('/registro', data={
            'nombre': 'Pedro FechaAntigua',
            'email': f'pedro_antigua_{datetime.now().timestamp()}@test.com',
            'fecha_nacimiento': fecha_antigua,
            'password': 'Secure@123456',
            'confirmar_password': 'Secure@123456'
        })
        
        body = response.get_data(as_text=True)
        print(f"Status: {response.status_code}")
        if 'mas de 150' in body or 'más de 150' in body:
            print("RESULTADO: Validacion correcta, fecha muy antigua rechazada")
            return True
        else:
            print("RESULTADO: No se validó correctamente")
            return False

def test_registro_menor_edad():
    """Prueba con usuario menor a 13 años (debe fallar)"""
    print("\n=== PRUEBA 4: Registro con menor de edad (debe fallar) ===")
    
    with app.test_client() as client:
        # Fecha de hace 10 años (menor de 13)
        fecha_menor = (date.today() - timedelta(days=10*365)).strftime('%Y-%m-%d')
        response = client.post('/registro', data={
            'nombre': 'Sofia Menor',
            'email': f'sofia_menor_{datetime.now().timestamp()}@test.com',
            'fecha_nacimiento': fecha_menor,
            'password': 'Secure@123456',
            'confirmar_password': 'Secure@123456'
        })
        
        body = response.get_data(as_text=True)
        print(f"Status: {response.status_code}")
        if 'al menos 13 anos' in body or 'al menos 13 años' in body:
            print("RESULTADO: Validacion correcta, menor de edad rechazado")
            return True
        else:
            print("RESULTADO: No se validó correctamente")
            return False

def test_registro_sin_fecha():
    """Prueba sin fecha (debe fallar)"""
    print("\n=== PRUEBA 5: Registro sin fecha de nacimiento (debe fallar) ===")
    
    with app.test_client() as client:
        response = client.post('/registro', data={
            'nombre': 'Ana SinFecha',
            'email': f'ana_sinfecha_{datetime.now().timestamp()}@test.com',
            'password': 'Secure@123456',
            'confirmar_password': 'Secure@123456'
        })
        
        body = response.get_data(as_text=True)
        print(f"Status: {response.status_code}")
        if 'obligatoria' in body:
            print("RESULTADO: Validacion correcta, fecha faltante rechazada")
            return True
        else:
            print("RESULTADO: No se validó correctamente")
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("PRUEBAS DE VALIDACION DE FECHA DE NACIMIENTO")
    print("=" * 60)
    
    resultados = []
    resultados.append(("Fecha valida", test_registro_con_fecha()))
    resultados.append(("Fecha futura", test_registro_fecha_futura()))
    resultados.append(("Fecha muy antigua", test_registro_fecha_muy_antigua()))
    resultados.append(("Menor de edad", test_registro_menor_edad()))
    resultados.append(("Sin fecha", test_registro_sin_fecha()))
    
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    for nombre, resultado in resultados:
        estado = "[OK]" if resultado else "[FAIL]"
        print(f"{estado} {nombre}")
    
    exitosas = sum(1 for _, r in resultados if r)
    print(f"\nPruebas exitosas: {exitosas}/{len(resultados)}")
