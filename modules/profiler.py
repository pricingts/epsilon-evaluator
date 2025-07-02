# modules/profiler.py
from __future__ import annotations
import os, openai, pandas as pd, textwrap
from dotenv import load_dotenv ; load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_PROMPT = textwrap.dedent("""
    Eres consultor senior de talento en logística internacional y dominas
    la metodología ÉPSILON. Con las puntuaciones 0-500 de cada módulo,
    redacta UN SOLO PÁRRAFO (máx. 180 palabras) que incluya:

    • síntesis de fortalezas, riesgos y estilo predominante
    • EXACTAMENTE 3 cargos sugeridos en un freight forwarder, con una
      muy breve justificación tras cada cargo (≈ 8-10 palabras).

    Estructura ejemplo (todo corrido):
    «Perfil: … Riesgos: … Recomendado para: Cargo 1 – …; Cargo 2 – …;
    Cargo 3 – ….»

    Devuelve SOLO el párrafo sin listas ni saltos de línea.
""").strip()


def build_prompt(row: pd.Series) -> str:
    lines = []
    for col in row.index:
        if col.startswith("Módulo"):
            val = row[col]
            if pd.notna(val):                # ← solo si hay valor
                lines.append(f"{col}: {int(round(val))}")
    scores_blob = "\n".join(lines) if lines else "Sin datos aún"

    return f"{BASE_PROMPT}\n\n=== SCORES ===\n{scores_blob}\n====="


def get_profile_paragraph(row: pd.Series) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        messages=[{"role": "user", "content": build_prompt(row)}],
    )
    return resp.choices[0].message.content.strip()
