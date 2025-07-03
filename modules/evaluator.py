from dotenv import load_dotenv
load_dotenv()           # busca automáticamente el .env y exporta variables
import os
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
import pandas as pd
import numpy as np
from tqdm.auto import tqdm 
import time
import json

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


def call_openai_and_parse_score(prompt: str, max_retries: int = 3, delay: float = 2.0) -> float:
    """
    Llama al modelo GPT y extrae solo el score_epsilon.
    Si falla, reintenta hasta max_retries veces. Si todos fallan, devuelve np.nan.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": "Piensa paso a paso internamente, pero responde con un JSON válido con una clave: score_epsilon."
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"} 
            )

            result = response.choices[0].message.content.strip()

            data = json.loads(result)

            score = data.get("score_epsilon", None)

            if isinstance(score, (int, float)):
                return float(score)

        except Exception as err:
            print(f"⚠️ Intento {attempt}/{max_retries} fallido: {err}")

        time.sleep(delay)

    print("⚠️ No se pudo obtener score válido tras varios intentos.")
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
