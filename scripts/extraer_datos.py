#!/usr/bin/env python3
"""
Extrae las tablas relevantes de la BD (Postgres/Neon) a CSV crudo en data/raw/.

Uso: python scripts/extraer_datos.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SQLALCHEMY_ECHO'] = 'False'

import pandas as pd

from app import create_app, db

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw')

TABLAS = [
    'mascotas',
    'solicitudes_adopcion',
    'donaciones',
    'donaciones_items',
    'reportes',
    'voluntariados',
    'solicitudes_voluntariado',
]


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    app, _ = create_app()

    with app.app_context():
        for tabla in TABLAS:
            df = pd.read_sql_table(tabla, db.engine)
            destino = os.path.join(DATA_DIR, f'{tabla}.csv')
            df.to_csv(destino, index=False)
            print(f'{tabla}: {len(df)} filas -> {destino}')


if __name__ == '__main__':
    main()
