from dotenv import load_dotenv
load_dotenv()           # busca automáticamente el .env y exporta variables
import os
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
import pandas as pd
import numpy as np
from tqdm.auto import tqdm 

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_prompt(module_name: str, rubric_text: str, answers: dict) -> str:
    answers_blob = "\n".join(f"{k}: {v}" for k, v in answers.items())
    return (
        f"Eres un evaluador del Sistema ÉPSILON.\n"
        f"Usa la siguiente rúbrica para calificar el {module_name}.\n\n"
        f"{rubric_text}\n\n"
        f"=== RESPUESTAS DEL CANDIDATO ===\n{answers_blob}\n"
        f"================================\n\n"
        f"Devuélveme únicamente el puntaje total en la escala ÉPSILON."
    )


def call_openai_and_parse_score(prompt: str) -> float:
    """Envía prompt y devuelve el primer número que encuentre en la respuesta."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Piensa paso a paso internamente, "
                        "pero responde con **solo** el puntaje numérico."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        text = response.choices[0].message.content.strip()
    except Exception as err:
        print("❌ Error en llamada a OpenAI:", err)
        return np.nan

    for tok in text.replace(",", ".").split():
        try:
            return float(tok)
        except ValueError:
            continue
    print("⚠️  No se detectó número en:", text)
    return np.nan


def evaluate_module_batch(
    df: pd.DataFrame, module_name: str, rubric_text: str, repetitions: int = 1
) -> pd.DataFrame:
    """Calcula N puntajes por candidato, luego media y desviación."""
    rows_out = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc=module_name):
        scores = [
            call_openai_and_parse_score(
                build_prompt(module_name, rubric_text, row.to_dict())
            )
            for _ in range(repetitions)
        ]
        rows_out.append(
            {
                **row.to_dict(),
                **{f"score_run_{i+1}": s for i, s in enumerate(scores)},
                "mean_score": np.nanmean(scores),
                "std_score": np.nanstd(scores),
            }
        )
    return pd.DataFrame(rows_out)
