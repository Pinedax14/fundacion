"""
Módulo de rutas para generación de reportes PDF
Contiene las rutas para generar diferentes tipos de reportes
Requiere rol de administrador
"""

from datetime import datetime
from flask import send_file, flash, redirect, url_for, session
from app.rutas.pdf_generator import PDFGenerator
from app.services.admin_data_service import AdminDataStructureService
from app.rutas.decoradores import admin_required_factory


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
        self.admin_data_service = AdminDataStructureService()
        self.admin_required = admin_required_factory(app)
        self._registrar_rutas()

    def _registrar_rutas(self):
        """Registra todas las rutas de reportes PDF"""
        self.app.add_url_rule('/reporte/usuarios', 'reporte_usuarios',
                             self.admin_required(self.reporte_usuarios), methods=['GET'])
        self.app.add_url_rule('/reporte/mascotas', 'reporte_mascotas',
                             self.admin_required(self.reporte_mascotas), methods=['GET'])
        self.app.add_url_rule('/reporte/donaciones', 'reporte_donaciones',
                             self.admin_required(self.reporte_donaciones), methods=['GET'])
        self.app.add_url_rule('/reporte/maltrato', 'reporte_maltrato',
                             self.admin_required(self.reporte_maltrato), methods=['GET'])

    def reporte_usuarios(self):
        """
        Genera un reporte PDF con la lista de usuarios registrados
        Solo accessibles por administradores
        """
        try:
            usuarios_linkedlist = self.admin_data_service.cargar_usuarios_en_linkedlist()
            usuarios = [
                (
                    u['id'],
                    u['nombre'],
                    u['email'],
                    u['password'],
                    u['fecha_registro'],
                    u['rol']
                )
                for u in usuarios_linkedlist.to_list()
            ]

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

    def reporte_mascotas(self):
        """
        Genera un reporte PDF con la lista de mascotas en el sistema
        Solo accessibles por administradores
        """
        try:
            mascotas_linkedlist = self.admin_data_service.cargar_mascotas_en_linkedlist()
            mascotas = [
                (
                    m['id'],
                    m['nombre'],
                    m['especie'],
                    m['raza'],
                    m['edad'],
                    m['sexo'],
                    m['descripcion'],
                    m['foto_url'],
                    m['estado'],
                    m['fecha_ingreso']
                )
                for m in mascotas_linkedlist.to_list()
            ]

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

    def reporte_donaciones(self):
        """
        Genera un reporte PDF con la lista de donaciones
        Solo accessibles por administradores
        """
        try:
            donaciones_linkedlist = self.admin_data_service.cargar_donaciones_en_linkedlist()
            donaciones = [
                (
                    d['id'],
                    d['nombre_donante'],
                    d['contacto_email'],
                    d['tipo_donacion'],
                    d['descripcion_donacion'],
                    d['fecha_donacion'],
                    d['estado_entrega']
                )
                for d in donaciones_linkedlist.to_list()
            ]

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

    def reporte_maltrato(self):
        """
        Genera un reporte PDF con la lista de reportes de maltrato animal
        Solo accessibles por administradores
        """
        try:
            reportes_queue = self.admin_data_service.cargar_reportes_en_queue()
            reportes = []
            while len(reportes_queue) > 0:
                reportes.append(reportes_queue.dequeue())

            reportes = [
                (
                    r['id'],
                    r['ubicacion'],
                    r['descripcion_incidente'],
                    r['foto_evidencia_url'],
                    r['fecha_reporte'],
                    r['estado_reporte']
                )
                for r in reportes
            ]

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
