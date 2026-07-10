#!/usr/bin/env python3
"""
Limpia los CSV crudos de data/raw/ y guarda versiones procesadas en data/processed/.

Reglas aplicadas (documentadas para el informe EDA):
- Fechas: se parsean a datetime; las que no parsean quedan NaT (no se eliminan filas por esto).
- Texto categórico (especie, sexo, estado, etc.): trim + capitalización consistente.
- Duplicados: se eliminan por 'id' si la columna existe.
- Nulos: no se imputan valores — se dejan explícitos (NaN) para que el EDA los muestre
  como parte de la calidad real de los datos, en vez de esconderlos.

Uso: python scripts/limpieza_datos.py
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

RANGO_INGRESOS_VALIDO = re.compile(r'^\d+-\d+$|^\d+\+$')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

COLUMNAS_FECHA = {
    'mascotas': ['fecha_ingreso'],
    'solicitudes_adopcion': ['fecha_solicitud'],
    'donaciones': ['fecha_donacion'],
    'donaciones_items': ['fecha_registro'],
    'reportes': ['fecha_reporte'],
    'voluntariados': ['fecha_registro'],
    'solicitudes_voluntariado': ['fecha_solicitud'],
}

COLUMNAS_CATEGORICAS = {
    'mascotas': ['especie', 'sexo', 'estado'],
    'solicitudes_adopcion': ['estado'],
    'donaciones_items': ['tipo_item', 'estado_entrega'],
    'reportes': ['estado'],
    'solicitudes_voluntariado': ['estado', 'franja_dias', 'franja_horaria'],
}


def limpiar_tabla(nombre, df):
    for col in COLUMNAS_FECHA.get(nombre, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    for col in COLUMNAS_CATEGORICAS.get(nombre, []):
        if col in df.columns:
            df[col] = df[col].astype('string').str.strip().str.capitalize()

    if nombre == 'solicitudes_adopcion' and 'ingresos' in df.columns:
        # La columna 'ingresos' era INTEGER antes de migrate_ingresos_type.py: las
        # solicitudes previas a esa migración quedaron con el entero crudo (ej.
        # "2147483647", un sentinel de overflow) en vez de un rango "min-max"
        # válido. Se marcan explícitamente en vez de descartarlas.
        es_valido = df['ingresos'].astype('string').str.match(RANGO_INGRESOS_VALIDO)
        n_legacy = (~es_valido).sum()
        if n_legacy:
            print(f'  {nombre}: {n_legacy} valores de "ingresos" con formato legado (pre-migración), marcados como legacy_invalido')
        df['ingresos'] = df['ingresos'].where(es_valido, other='legacy_invalido')

    if 'id' in df.columns:
        antes = len(df)
        df = df.drop_duplicates(subset='id', keep='first')
        eliminados = antes - len(df)
        if eliminados:
            print(f'  {nombre}: {eliminados} duplicados eliminados')

    return df


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    for archivo in sorted(os.listdir(RAW_DIR)):
        if not archivo.endswith('.csv'):
            continue
        nombre = archivo[:-4]
        df = pd.read_csv(os.path.join(RAW_DIR, archivo))
        df = limpiar_tabla(nombre, df)

        nulos = df.isna().sum()
        nulos = nulos[nulos > 0]
        if not nulos.empty:
            print(f'{nombre}: nulos por columna -> {dict(nulos)}')

        destino = os.path.join(PROCESSED_DIR, archivo)
        df.to_csv(destino, index=False)
        print(f'{nombre}: {len(df)} filas limpias -> {destino}')


if __name__ == '__main__':
    main()
