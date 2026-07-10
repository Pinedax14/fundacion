"""
Tests para el blueprint de API JSON (/api/v1)
"""

from datetime import datetime

from app.models import db, Mascota, Donacion, Item_Donacion, Reporte, Usuario, SolicitudAdopcion


class TestApiMascotas:
    """GET /api/v1/mascotas es público"""

    def test_lista_vacia(self, client):
        resp = client.get('/api/v1/mascotas')
        assert resp.status_code == 200
        assert resp.get_json() == {'total': 0, 'mascotas': []}

    def test_lista_y_filtra(self, app, client):
        with app.app_context():
            db.session.add(Mascota(
                nombre='Firulais', especie='perro', raza='criollo',
                edad=12, sexo='M', estado='Disponible',
            ))
            db.session.add(Mascota(
                nombre='Michi', especie='gato', raza='criollo',
                edad=6, sexo='F', estado='Disponible',
            ))
            db.session.commit()

        resp = client.get('/api/v1/mascotas')
        assert resp.status_code == 200
        assert resp.get_json()['total'] == 2

        resp = client.get('/api/v1/mascotas?especie=gato')
        data = resp.get_json()
        assert data['total'] == 1
        assert data['mascotas'][0]['nombre'] == 'Michi'


class TestApiDonacionesResumen:
    """GET /api/v1/donaciones/resumen requiere sesión de administrador"""

    def test_sin_sesion_devuelve_401(self, client):
        resp = client.get('/api/v1/donaciones/resumen')
        assert resp.status_code == 401

    def test_usuario_no_admin_devuelve_403(self, client):
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['rol'] = 'user'
        resp = client.get('/api/v1/donaciones/resumen')
        assert resp.status_code == 403

    def test_admin_recibe_resumen(self, app, client):
        with app.app_context():
            db.session.add(Donacion(cantidad=50000, fecha_donacion=datetime(2026, 1, 15)))
            donacion_con_items = Donacion(cantidad=30000, fecha_donacion=datetime(2026, 1, 20))
            db.session.add(donacion_con_items)
            db.session.commit()
            db.session.add(Item_Donacion(
                donacion_id=donacion_con_items.id, tipo_item='alimento', cantidad=3,
            ))
            db.session.commit()

        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['rol'] = 'admin'

        resp = client.get('/api/v1/donaciones/resumen')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total_monetario'] == 80000
        assert data['total_donaciones'] == 2
        assert data['donaciones_por_mes'] == [{'mes': '2026-01', 'monto': 80000, 'cantidad': 2}]
        assert data['items_por_tipo'] == [{'tipo': 'alimento', 'cantidad': 1}]


class TestApiAdopcionesResumen:
    """GET /api/v1/adopciones/resumen requiere sesión de administrador"""

    def test_sin_sesion_devuelve_401(self, client):
        resp = client.get('/api/v1/adopciones/resumen')
        assert resp.status_code == 401

    def test_admin_recibe_resumen(self, app, client):
        with app.app_context():
            usuario = Usuario(nombre='Ana', email='ana@example.com', password='hash')
            mascota = Mascota(
                nombre='Firulais', especie='perro', raza='criollo',
                edad=12, sexo='M', estado='En proceso',
            )
            db.session.add_all([usuario, mascota])
            db.session.commit()

            db.session.add(SolicitudAdopcion(
                usuario_id=usuario.id, mascota_id=mascota.id,
                estado='pendiente', fecha_solicitud=datetime(2026, 1, 10),
            ))
            db.session.add(SolicitudAdopcion(
                usuario_id=usuario.id, mascota_id=mascota.id,
                estado='aprobada', fecha_solicitud=datetime(2026, 1, 20),
            ))
            db.session.commit()

        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['rol'] = 'admin'

        resp = client.get('/api/v1/adopciones/resumen')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total_solicitudes'] == 2
        assert data['adopciones_por_mes'] == [{'mes': '2026-01', 'cantidad': 2}]
        assert {'estado': 'pendiente', 'cantidad': 1} in data['por_estado']
        assert {'estado': 'aprobada', 'cantidad': 1} in data['por_estado']


class TestApiReportes:
    """GET /api/v1/reportes requiere sesión de administrador"""

    def test_sin_sesion_devuelve_401(self, client):
        resp = client.get('/api/v1/reportes')
        assert resp.status_code == 401

    def test_admin_recibe_lista(self, app, client):
        with app.app_context():
            db.session.add(Reporte(
                ubicacion='Calle 10 #5-20',
                descripcion_incidente='Perro abandonado',
                estado='recibido',
            ))
            db.session.commit()

        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['rol'] = 'admin'

        resp = client.get('/api/v1/reportes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] == 1
        assert data['reportes'][0]['ubicacion'] == 'Calle 10 #5-20'
