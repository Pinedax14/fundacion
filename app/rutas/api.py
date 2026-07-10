"""
API JSON (v1) de la aplicación.

Expone en formato JSON los mismos datos que ya sirve la app en HTML,
reutilizando los services/modelos existentes, para alimentar gráficos
(Chart.js) y cualquier consumo externo (apps móviles, scripts de análisis).
"""

from functools import wraps

from flask import Blueprint, jsonify, request, session

from app.models import Donacion, Item_Donacion, Reporte, SolicitudAdopcion
from app.services.admin_data_service import AdminDataStructureService

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

admin_data_service = AdminDataStructureService()


def admin_required_json(f):
    """Protege un endpoint de API exigiendo sesión de administrador.

    Responde 401/403 en JSON en vez de redirigir a `/login`, porque un
    cliente de API no puede seguir una redirección HTML.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'loggedin' not in session:
            return jsonify(error='No autenticado'), 401
        if session.get('rol') != 'admin':
            return jsonify(error='Acceso no autorizado'), 403
        return f(*args, **kwargs)
    return decorated


def _mascota_a_dict(mascota):
    # La query cruda (`text(...)`) devuelve fecha_ingreso como datetime en
    # Postgres pero como string en SQLite (usado en tests), así que se
    # normaliza aceptando ambos casos.
    fecha_ingreso = mascota.get('fecha_ingreso')
    if hasattr(fecha_ingreso, 'isoformat'):
        fecha_ingreso = fecha_ingreso.isoformat()

    return {
        'id': mascota.get('id'),
        'nombre': mascota.get('nombre'),
        'especie': mascota.get('especie'),
        'raza': mascota.get('raza'),
        'edad': mascota.get('edad'),
        'sexo': mascota.get('sexo'),
        'descripcion': mascota.get('descripcion'),
        'foto_url': mascota.get('foto_url'),
        'estado': mascota.get('estado'),
        'fecha_ingreso': fecha_ingreso,
    }


@api_bp.route('/mascotas', methods=['GET'])
def listar_mascotas():
    """
    GET /api/v1/mascotas

    Query params opcionales: especie, sexo, estado (mismo criterio de
    filtrado que la vista HTML /filtrar_mascotas).
    """
    especie = request.args.get('especie', '').strip().lower()
    sexo = request.args.get('sexo', '').strip().upper()
    estado = request.args.get('estado', '').strip().lower()

    mascotas = admin_data_service.cargar_mascotas_en_linkedlist().to_list()

    if especie:
        mascotas = [m for m in mascotas if m.get('especie', '').lower() == especie]
    if sexo:
        mascotas = [m for m in mascotas if m.get('sexo', '').upper() == sexo]
    if estado:
        mascotas = [m for m in mascotas if m.get('estado', '').lower() == estado]

    return jsonify(total=len(mascotas), mascotas=[_mascota_a_dict(m) for m in mascotas])


@api_bp.route('/donaciones/resumen', methods=['GET'])
@admin_required_json
def resumen_donaciones():
    """
    GET /api/v1/donaciones/resumen

    Resumen para dashboards: total donado en dinero, serie mensual
    (monto y cantidad) y conteo de donaciones en especie por tipo.
    """
    donaciones = Donacion.query.all()
    items = Item_Donacion.query.all()

    total_monetario = sum(d.cantidad or 0 for d in donaciones)

    por_mes = {}
    for d in donaciones:
        if not d.fecha_donacion:
            continue
        mes = d.fecha_donacion.strftime('%Y-%m')
        registro = por_mes.setdefault(mes, {'monto': 0.0, 'cantidad': 0})
        registro['monto'] += d.cantidad or 0
        registro['cantidad'] += 1

    por_tipo_item = {}
    for item in items:
        por_tipo_item[item.tipo_item] = por_tipo_item.get(item.tipo_item, 0) + 1

    return jsonify(
        total_monetario=total_monetario,
        total_donaciones=len(donaciones),
        donaciones_por_mes=[
            {'mes': mes, 'monto': datos['monto'], 'cantidad': datos['cantidad']}
            for mes, datos in sorted(por_mes.items())
        ],
        items_por_tipo=[
            {'tipo': tipo, 'cantidad': cantidad}
            for tipo, cantidad in sorted(por_tipo_item.items())
        ],
    )


@api_bp.route('/adopciones/resumen', methods=['GET'])
@admin_required_json
def resumen_adopciones():
    """
    GET /api/v1/adopciones/resumen

    Resumen para dashboards: solicitudes de adopción por mes y conteo
    por estado (pendiente/aprobada/rechazada).
    """
    solicitudes = SolicitudAdopcion.query.all()

    por_mes = {}
    por_estado = {}
    for s in solicitudes:
        if s.fecha_solicitud:
            mes = s.fecha_solicitud.strftime('%Y-%m')
            por_mes[mes] = por_mes.get(mes, 0) + 1
        estado = (s.estado or 'sin_estado').lower()
        por_estado[estado] = por_estado.get(estado, 0) + 1

    return jsonify(
        total_solicitudes=len(solicitudes),
        adopciones_por_mes=[
            {'mes': mes, 'cantidad': cantidad}
            for mes, cantidad in sorted(por_mes.items())
        ],
        por_estado=[
            {'estado': estado, 'cantidad': cantidad}
            for estado, cantidad in sorted(por_estado.items())
        ],
    )


@api_bp.route('/reportes', methods=['GET'])
@admin_required_json
def listar_reportes():
    """
    GET /api/v1/reportes

    Lista de reportes de maltrato animal. Requiere sesión de administrador:
    incluye ubicación y evidencia de casos sensibles.
    """
    estado = request.args.get('estado', '').strip().lower()

    reportes = Reporte.query.order_by(Reporte.fecha_reporte.desc()).all()
    if estado:
        reportes = [r for r in reportes if (r.estado or '').lower() == estado]

    return jsonify(total=len(reportes), reportes=[
        {
            'id': r.id,
            'ubicacion': r.ubicacion,
            'descripcion_incidente': r.descripcion_incidente,
            'foto_evidencia_url': r.foto_evidencia_url,
            'estado': r.estado,
            'fecha_reporte': r.fecha_reporte.isoformat() if r.fecha_reporte else None,
        }
        for r in reportes
    ])
