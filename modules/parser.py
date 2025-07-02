"""
parser.py  – helpers para seleccionar columnas de cada módulo
y conservar las columnas que identifican al participante.
"""

from __future__ import annotations
import re
import pandas as pd

# Personaliza esta lista si tus identificadores cambian
ID_COLS = ["Email Address", "Full Name"]

def detect_module_from_sheet(sheet_name: str) -> str | None:
    """Convierte 'ÉPSILON - MOD3' o 'MOD9R Results' → 'Módulo 3' / 'Módulo 9R'."""
    m = re.search(r"MOD(\d+[R]?)", sheet_name.upper())
    return f"Módulo {m.group(1)}" if m else None


def extract_answers_by_module(
    df: pd.DataFrame,
    module_code: str,
    id_cols: list[str] = ID_COLS,
) -> pd.DataFrame:
    """
    Devuelve únicamente:
      • columnas que comienzan con el prefijo del módulo (MOD1_, MOD2_, …)
      • + columnas de identidad definidas en ID_COLS (si existen en la hoja)
    """
    prefix = module_code.split()[0].upper().replace("Ó", "O").replace(" ", "")
    mod_cols = [c for c in df.columns if c.strip().startswith(prefix)]
    ident_cols = [c for c in id_cols if c in df.columns]
    return df[ident_cols + mod_cols].copy()


def simplify_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Corta lo que hay después del primer '–' para dejar cabeceras compactas."""
    df.columns = [c.split("–")[0].strip() for c in df.columns]
    return df
