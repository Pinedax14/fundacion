# app/pdf_generator.py
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import io

class PDFGenerator:
    """Generador de reportes PDF para Almas con Cola"""
    
    def __init__(self):
        self.brand_color = colors.HexColor('#21808D')
        self.styles = getSampleStyleSheet()
    
    def _get_table_style(self):
        """Retorna el estilo estándar de tablas"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.brand_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ])
    
    def _create_header(self, titulo):
        """Crea el encabezado del reporte"""
        elements = []
        elements.append(Paragraph(f"{titulo} - Almas con Cola", self.styles['Title']))
        elements.append(Spacer(1, 8))
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
        elements.append(Paragraph(f"Fecha de generación: {fecha_actual}", self.styles['Normal']))
        elements.append(Spacer(1, 12))
        return elements
    
    def generar_reporte_usuarios(self, usuarios):
        """Genera reporte PDF de usuarios"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        elements = []
        
        # Encabezado
        elements.extend(self._create_header("Reporte de Usuarios Registrados"))
        
        # Datos de la tabla
        datos_tabla = [["ID", "Nombre", "Email", "Rol", "Fecha Registro"]]
        
        for u in usuarios:
            datos_tabla.append([
                str(u[0]),  # id
                str(u[1]),  # nombre
                str(u[2]),  # email
                str(u[5]),  # rol
                str(u[4])   # fecha_registro
            ])
        
        # Crear y estilizar tabla
        tabla = Table(datos_tabla, colWidths=[50, 150, 200, 80, 150])
        tabla.setStyle(self._get_table_style())
        elements.append(tabla)
        
        # Agregar total de usuarios
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Total de usuarios registrados: {len(usuarios)}", self.styles['Normal']))
        
        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generar_reporte_mascotas(self, mascotas):
        """Genera reporte PDF de mascotas
        Campos: id, nombre, especie, raza, edad, sexo, descripcion, foto_url, estado, fecha_ingreso
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        elements = []
        
        # Encabezado
        elements.extend(self._create_header("Reporte de Mascotas"))
        
        # Datos de la tabla
        datos_tabla = [["ID", "Nombre", "Especie", "Raza", "Edad", "Sexo", "Estado", "Fecha Ingreso"]]
        
        for m in mascotas:
            datos_tabla.append([
                str(m[0]),  # id
                str(m[1]),  # nombre
                str(m[2]),  # especie
                str(m[3]),  # raza
                str(m[4]),  # edad
                str(m[5]),  # sexo
                str(m[8]),  # estado
                str(m[9])   # fecha_ingreso
            ])
        
        tabla = Table(datos_tabla, colWidths=[30, 80, 70, 80, 50, 50, 80, 90])
        tabla.setStyle(self._get_table_style())
        elements.append(tabla)
        
        # Agregar estadísticas
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Total de mascotas registradas: {len(mascotas)}", self.styles['Normal']))
        
        # Contar por estado
        estados = {}
        for m in mascotas:
            estado = str(m[8])
            estados[estado] = estados.get(estado, 0) + 1
        
        for estado, cantidad in estados.items():
            elements.append(Paragraph(f"  • {estado}: {cantidad}", self.styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generar_reporte_donaciones(self, donaciones):
        """Genera reporte PDF de donaciones
        Campos: id, nombre_donante, contacto_email, tipo_donacion, descripcion_donacion, 
                fecha_donacion, estado_entrega
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        elements = []
        
        elements.extend(self._create_header("Reporte de Donaciones"))
        
        # Datos de la tabla
        datos_tabla = [["ID", "Donante", "Email", "Tipo", "Estado", "Fecha"]]
        
        for d in donaciones:
            # Truncar descripción si es muy larga
            tipo = str(d[3]) if len(str(d[3])) <= 20 else str(d[3])[:17] + "..."
            
            datos_tabla.append([
                str(d[0]),  # id
                str(d[1]),  # nombre_donante
                str(d[2]),  # contacto_email
                tipo,       # tipo_donacion
                str(d[6]),  # estado_entrega
                str(d[5])   # fecha_donacion
            ])
        
        tabla = Table(datos_tabla, colWidths=[30, 120, 150, 120, 100, 110])
        tabla.setStyle(self._get_table_style())
        elements.append(tabla)
        
        # Estadísticas
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Total de donaciones: {len(donaciones)}", self.styles['Normal']))
        
        # Contar por estado de entrega
        estados = {}
        for d in donaciones:
            estado = str(d[6])
            estados[estado] = estados.get(estado, 0) + 1
        
        for estado, cantidad in estados.items():
            elements.append(Paragraph(f"  • {estado}: {cantidad}", self.styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generar_reporte_maltrato(self, reportes):
        """Genera reporte PDF de reportes de maltrato
        Campos: id, ubicacion, descripcion_incidente, foto_evidencia_url, fecha_reporte, estado_reporte
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        elements = []
        
        elements.extend(self._create_header("Reportes de Maltrato Animal"))
        
        # Datos de la tabla
        datos_tabla = [["ID", "Ubicación", "Descripción Incidente", "Estado", "Fecha Reporte"]]
        
        for r in reportes:
            # Truncar descripción si es muy larga
            descripcion = str(r[2])
            if len(descripcion) > 60:
                descripcion = descripcion[:57] + "..."
            
            datos_tabla.append([
                str(r[0]),  # id
                str(r[1]),  # ubicacion
                descripcion,  # descripcion_incidente
                str(r[5]),  # estado_reporte
                str(r[4])   # fecha_reporte
            ])
        
        tabla = Table(datos_tabla, colWidths=[30, 120, 250, 100, 100])
        tabla.setStyle(self._get_table_style())
        elements.append(tabla)
        
        # Estadísticas
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Total de reportes: {len(reportes)}", self.styles['Normal']))
        
        # Contar por estado
        estados = {}
        for r in reportes:
            estado = str(r[5])
            estados[estado] = estados.get(estado, 0) + 1
        
        for estado, cantidad in estados.items():
            elements.append(Paragraph(f"  • {estado}: {cantidad}", self.styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
