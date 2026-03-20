#!/usr/bin/env python3
"""
Script para verificar conteos de registros en las tablas principales
"""
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Desactivar logs de SQLAlchemy
os.environ['SQLALCHEMY_ECHO'] = 'False'

from app import create_app

def main():
    app, db = create_app()
    with app.app_context():
        from app import db
        from sqlalchemy import text

        print("=== CONTEO DE REGISTROS EN TABLAS ===")

        tablas = [
            ('usuarios', 'Usuarios registrados'),
            ('mascotas', 'Mascotas disponibles'),
            ('solicitudes_adopcion', 'Solicitudes de adopción'),
            ('reportes', 'Reportes de maltrato'),
            ('solicitudes_voluntariado', 'Solicitudes de voluntariado'),
            ('donaciones_items', 'Ítems de donación')
        ]

        for tabla, descripcion in tablas:
            try:
                result = db.session.execute(text(f'SELECT COUNT(*) as count FROM {tabla}')).fetchone()
                print(f"{descripcion}: {result.count} registros")
            except Exception as e:
                print(f"Error en {tabla}: {e}")

        print("\n=== VERIFICACIÓN COMPLETA ===")

if __name__ == '__main__':
    main()