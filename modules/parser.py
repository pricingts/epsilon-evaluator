"""
parser.py  – helpers para seleccionar columnas de cada módulo
y conservar las columnas que identifican al participante.
"""

from __future__ import annotations
import re
import pandas as pd
from typing import List

# Personaliza esta lista si tus identificadores cambian
ID_COLS = ["Email Address", "Full Name"]

def detect_module_from_sheet(sheet_name: str) -> str | None:
    """Convierte 'ÉPSILON - MOD3' o 'MOD9R Results' → 'Módulo 3' / 'Módulo 9R'."""
    m = re.search(r"MOD(\d+[R]?)", sheet_name.upper())
    return f"Módulo {m.group(1)}" if m else None


def extract_answers_by_module(
    df: pd.DataFrame,
    module_code: str,
    id_cols: List[str] = ID_COLS,
) -> pd.DataFrame:
    """
    Devuelve:
      · columnas propias del módulo (MOD9_, EPS9A_, EPS9R_, …)
      · columnas de identidad presentes (Email Address, Full Name, etc.).
    """
    # «Módulo 9» → 9   ·  «Módulo 9R» → 9R
    num = re.search(r"\d+[R]?", module_code, flags=re.I).group(0)

    # Acepta MOD… o EPS…, con letras opcionales tras el número (A, B, R…)
    prefix_re = re.compile(
        rf"^\s*(?:MOD|EPS)\s*{num.rstrip('R')}[A-Z]*\s*[_\-\u2013\u2014\s]",
        flags=re.I,
    )

    mod_cols   = [c for c in df.columns if prefix_re.match(c)]
    ident_cols = [c for c in id_cols if c in df.columns]

    return df[ident_cols + mod_cols].copy()


def simplify_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Corta lo que hay después del primer '–' para dejar cabeceras compactas."""
    df.columns = [c.split("–")[0].strip() for c in df.columns]
    return df
