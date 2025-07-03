from __future__ import annotations
from pathlib import Path
import os
import pandas as pd

from modules.parser import (
    extract_answers_by_module,
    simplify_columns,
    detect_module_from_sheet,
    ID_COLS,
)
from modules.evaluator import evaluate_module_batch
from modules.profiler import get_profile_paragraph
from prompts.rubrics import RUBRICS


# ───────────────────────── CONFIG POR DEFECTO ──────────────────────────
DEFAULT_INPUT  = Path("data/RESPUESTAS EPSILON.xlsx")
DEFAULT_OUTPUT = Path("outputs/calificaciones_epsilion.xlsx")


# ───────────────────────── FUNCIÓN PRINCIPAL ───────────────────────────
def run_pipeline(
    input_file: Path | str | None = None,
    output_file: Path | str | None = None,
    repetitions: int = 2,
) -> None:

    INPUT_FILE  = Path(input_file)  if input_file  else DEFAULT_INPUT
    OUTPUT_FILE = Path(output_file) if output_file else DEFAULT_OUTPUT

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"No se encontró {INPUT_FILE}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    xlsx   = pd.ExcelFile(INPUT_FILE)
    writer = pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl")

    summary_frames: list[pd.DataFrame] = []

    for sheet in xlsx.sheet_names:
        module_key = detect_module_from_sheet(sheet)
        if module_key not in RUBRICS:
            continue  

        print(f"📝 Procesando '{sheet}' → {module_key}")
        df_raw = pd.read_excel(xlsx, sheet_name=sheet)
        df_mod = simplify_columns(extract_answers_by_module(df_raw, module_key))

        df_res = evaluate_module_batch(
            df_mod,
            module_key,
            RUBRICS[module_key],
            repetitions=repetitions,
        )
        df_res.to_excel(writer, sheet_name=module_key, index=False)

        id_cols_present = [c for c in ID_COLS if c in df_res.columns]
        summary_frames.append(
            df_res[id_cols_present + ["mean_score"]]
            .rename(columns={"mean_score": module_key})
        )

    if summary_frames:
        big = pd.concat(summary_frames, ignore_index=True)

        big["__email_key"] = big["Email Address"].str.lower().str.strip()

        num_cols = big.select_dtypes("number").columns.tolist()
        agg_map  = {c: "mean" for c in num_cols}
        agg_map["Email Address"] = "first"
        agg_map["Full Name"] = lambda s: (
            s.mode().iat[0] if not s.mode().empty else s.iloc[0]
        )

        grouped = big.groupby("__email_key", as_index=False).agg(agg_map)

        mod_cols = [c for c in grouped.columns if c.startswith("Módulo")]
        grouped["Promedio_Final"] = grouped[mod_cols].mean(axis=1, skipna=True)

        def classify(score):
            if pd.isna(score):
                return "Sin score"
            if score >= 450:
                return "🔥 REVELATION"
            if score >= 300:
                return "🚀 CHANGER"
            if score >= 150:
                return "🛠️ BUILDER"
            return "❌ DESCARTABLE"

        grouped["Categoría_ÉPSILON"] = grouped["Promedio_Final"].apply(classify)

        print("🧠  Generando perfiles GPT…")
        grouped["Perfil_Sugerido"] = grouped.apply(get_profile_paragraph, axis=1)

        ordered_cols = (
            ["Email Address", "Full Name"]
            + mod_cols
            + ["Promedio_Final", "Categoría_ÉPSILON", "Perfil_Sugerido"]
        )

        grouped[ordered_cols].to_excel(writer, sheet_name="Resumen", index=False)

    writer.close()
    print(f"✅ Resultados guardados en {OUTPUT_FILE}")

    return OUTPUT_FILE

if __name__ == "__main__":
    run_pipeline(repetitions=1)